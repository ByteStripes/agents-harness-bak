"""Read-only MSVC x86/x64 CRT entry heuristics; candidates are NOT proven entrypoints."""
import argparse
import json
import re
import struct
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('sample', type=Path)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    import pefile
    pe = pefile.PE(data=args.sample.read_bytes())
    if pe.FILE_HEADER.Machine == 0x8664:
        pattern = rb'\x48\x83\xec\x28\xe8....\x48\x83\xc4\x28\xe9....'
        call_disp, call_end, jump_disp, jump_end = 5, 9, 14, 18
    elif pe.FILE_HEADER.Machine == 0x14c:
        pattern = rb'\xe8....\xe9....\xcc\xcc'
        call_disp, call_end, jump_disp, jump_end = 1, 5, 6, 10
    else:
        parser.error('Only I386/AMD64 heuristics are implemented')
    records = []
    for section in pe.sections:
        if not section.Characteristics & 0x20000000:
            continue
        data = section.get_data()
        for match in re.finditer(pattern, data, re.S):
            rva = section.VirtualAddress + match.start()
            cookie = rva + call_end + struct.unpack_from('<i', match.group(), call_disp)[0]
            startup = rva + jump_end + struct.unpack_from('<i', match.group(), jump_disp)[0]
            records.append({'rva': hex(rva), 'va': hex(pe.OPTIONAL_HEADER.ImageBase+rva),
                            'section': section.Name.rstrip(b'\0').decode(errors='replace'),
                            'call_target_rva': hex(cookie), 'startup_target_rva': hex(startup),
                            'bytes': match.group().hex(),
                            'targets_in_image': all(0 <= v < pe.OPTIONAL_HEADER.SizeOfImage for v in (cookie, startup))})
    result = {'sample': str(args.sample.resolve()), 'machine':hex(pe.FILE_HEADER.Machine),'heuristic_only': True,
              'note': 'Validate disassembly, initialization and real execution; do not auto-patch.',
              'candidates': records}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open('x', encoding='utf-8') as dest:
        json.dump(result, dest, indent=2)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
