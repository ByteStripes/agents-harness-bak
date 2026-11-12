"""Optional legacy x64 emulator API/version-resource adapter; not a native OS hook."""
import argparse
import struct
import sys
from pathlib import Path

STATION = 0x6500


def firmware(self, symbol, rcx, rdx, r8, r9):
    from unpack.api_handlers import smbios_table
    provider = rcx & 0xffffffff
    details = {'compat_model': 'uefi_firmware', 'provider': hex(provider)}
    if provider == 0x4649524d:
        self.last_error = 50
        return 0, details
    if provider != 0x52534d42:
        return None, {**details, 'unsupported_provider': True}
    if symbol == 'enumsystemfirmwaretables':
        payload, output, capacity = struct.pack('<I',0), rdx, r8 & 0xffffffff
    else:
        if (rdx & 0xffffffff) != 0:
            self.last_error = 87
            return 0, details
        payload, output, capacity = smbios_table(), r8, r9 & 0xffffffff
    if not output or capacity < len(payload): return len(payload), details
    if not self.writable_range(output, len(payload)):
        self.last_error = 998
        return 0, details
    self.uc.mem_write(output, payload)
    return len(payload), details


def check_remote_debugger(self, symbol, rcx, rdx, r8, r9):
    if rcx != self.arch.mask:
        self.last_error = 6
        return 0, {'compat_model': 'current_process_debugger', 'invalid_handle': True}
    if not rdx or not self.writable_range(rdx, 4):
        self.last_error = 998
        return 0, {'compat_model': 'current_process_debugger', 'invalid_output': True}
    self.uc.mem_write(rdx, struct.pack('<I', 0))
    return 1, {'compat_model': 'current_process_debugger', 'debugger_present': False}


def get_station(self, symbol, rcx, rdx, r8, r9):
    return STATION, {'compat_model': 'interactive_window_station'}


def get_information(self, symbol, rcx, rdx, r8, r9):
    details = {'compat_model': 'window_station_flags', 'information_class': rdx & 0xffffffff}
    if rcx != STATION:
        self.last_error = 6
        return 0, details
    if (rdx & 0xffffffff) != 1:
        return None, {**details, 'unsupported_information_class': True}
    needed = self.stack_slot(4)
    if needed:
        if not self.writable_range(needed, 4):
            self.last_error = 998
            return 0, details
        self.uc.mem_write(needed, struct.pack('<I', 12))
    if (r9 & 0xffffffff) < 12:
        self.last_error = 122
        return 0, details
    if not r8 or not self.writable_range(r8, 12):
        self.last_error = 998
        return 0, details
    self.uc.mem_write(r8, struct.pack('<III', 0, 0, 1))
    return 1, details


def install():
    from unpack.api_handlers import ApiHandlers
    for name, handler, argc in [('getprocesswindowstation', get_station, 0),
                                ('enumsystemfirmwaretables', firmware, 3),
                                ('getsystemfirmwaretable', firmware, 4),
                                ('checkremotedebuggerpresent', check_remote_debugger, 2),
                                ('getuserobjectinformationa', get_information, 5),
                                ('getuserobjectinformationw', get_information, 5)]:
        # Do not override upstream implementations if a newer tool provides them.
        ApiHandlers._handlers.setdefault(name, (handler, argc))


def install_ntdll_resources(tracer):
    import pefile
    original = tracer.build_emu_module_blob
    def build(module_name, symbols, module_base, arch=tracer.MODE64):
        blob, assignments, stubs = original(module_name, symbols, module_base, arch)
        if module_name != 'ntdll.dll': return blob, assignments, stubs
        pe = pefile.PE(data=tracer.require_catalog().ntdll_bytes)
        destination = 0x60000
        versions = [e for e in pe.DIRECTORY_ENTRY_RESOURCE.entries if e.id == 16]
        if len(versions)!=1 or len(versions[0].directory.entries)!=1:
            raise ValueError('Expected one bundled ntdll version resource')
        name = versions[0].directory.entries[0]
        if name.id is None or len(name.directory.entries)!=1:
            raise ValueError('Expected numeric single-language version resource')
        lang = name.directory.entries[0]
        record = lang.data.struct
        data = pe.get_data(record.OffsetToData, record.Size)
        payload = bytearray(88)+data
        for offset in (0,24,48): struct.pack_into('<H',payload,offset+14,1)
        struct.pack_into('<II',payload,16,16,0x80000018)
        struct.pack_into('<II',payload,40,name.id,0x80000030)
        struct.pack_into('<II',payload,64,lang.id,72)
        struct.pack_into('<IIII',payload,72,destination+88,len(data),record.CodePage,0)
        if destination+len(payload)>len(blob): raise ValueError('Version resource too large')
        out = bytearray(blob)
        if any(out[destination:destination+len(payload)]):
            raise ValueError('Resource destination is occupied; unsupported upstream layout')
        out[destination:destination+len(payload)] = payload
        # The upstream synthetic optional header begins at 0x98.
        if pe.FILE_HEADER.Machine != arch.machine or out[0x98:0x9a] != struct.pack('<H',arch.magic):
            raise ValueError('Catalog/synthetic PE architecture mismatch')
        resource_directory = 0x118 if arch.bits == 64 else 0x108
        struct.pack_into('<II', out, resource_directory, destination, len(payload))
        return bytes(out), assignments, stubs
    tracer.build_emu_module_blob = build


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tool-root', required=True, type=Path)
    parser.add_argument('--ntdll-resources', action='store_true')
    parser.add_argument('unpack_args', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    root = args.tool_root.resolve(strict=True)
    if not (root/'unpack'/'tracer.py').is_file():
        parser.error('Expected vmp-lazy-unpack source root')
    forwarded = args.unpack_args
    if forwarded and forwarded[0] == '--': forwarded = forwarded[1:]
    if not forwarded: parser.error('Provide input and unpack arguments after --')
    if '--32bit' in forwarded: parser.error('This compatibility adapter was validated for x64 only')
    sys.path.insert(0, str(root))
    install()
    from unpack import tracer
    if args.ntdll_resources: install_ntdll_resources(tracer)
    sys.argv = ['unpack', *forwarded]
    tracer.main()


if __name__ == '__main__':
    main()
