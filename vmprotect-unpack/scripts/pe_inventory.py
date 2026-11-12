"""Read-only PE inventory and printable strings; requires pefile."""
import argparse
import hashlib
import json
import re
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('sample', type=Path)
    parser.add_argument('--out', required=True, type=Path, help='New output directory')
    args = parser.parse_args()
    import pefile
    data = args.sample.read_bytes()
    pe = pefile.PE(data=data)
    resources = []
    def walk_resources(directory, components=()):
        for entry in directory.entries:
            key = str(entry.name) if entry.name is not None else entry.id
            path = components + (key,)
            if hasattr(entry, 'directory'):
                walk_resources(entry.directory, path)
            elif hasattr(entry, 'data'):
                record = entry.data.struct
                payload = pe.get_data(record.OffsetToData, record.Size)
                resources.append({'path': path, 'rva': hex(record.OffsetToData),
                                  'size': record.Size, 'read_size': len(payload),
                                  'sha256': hashlib.sha256(payload).hexdigest()})
    if hasattr(pe, 'DIRECTORY_ENTRY_RESOURCE'):
        walk_resources(pe.DIRECTORY_ENTRY_RESOURCE)
    runtime_starts = [entry.struct.BeginAddress for entry in getattr(pe, 'DIRECTORY_ENTRY_EXCEPTION', [])]
    result = {
        'file': str(args.sample.resolve()), 'size': len(data),
        'sha256': hashlib.sha256(data).hexdigest(),
        'machine': hex(pe.FILE_HEADER.Machine),
        'dll': bool(pe.FILE_HEADER.Characteristics & 0x2000),
        'image_base': hex(pe.OPTIONAL_HEADER.ImageBase),
        'entry_rva': hex(pe.OPTIONAL_HEADER.AddressOfEntryPoint),
        'image_size': pe.OPTIONAL_HEADER.SizeOfImage,
        'dll_characteristics': hex(pe.OPTIONAL_HEADER.DllCharacteristics),
        'sections': [dict(name=s.Name.rstrip(b'\0').decode(errors='replace'),
                          rva=hex(s.VirtualAddress), virtual_size=s.Misc_VirtualSize,
                          raw_offset=s.PointerToRawData, raw_size=s.SizeOfRawData,
                          flags=hex(s.Characteristics), entropy=s.get_entropy())
                     for s in pe.sections],
        'directories': [dict(index=i, rva=hex(d.VirtualAddress), size=d.Size)
                        for i, d in enumerate(pe.OPTIONAL_HEADER.DATA_DIRECTORY)],
        'imports': [dict(dll=d.dll.decode(errors='replace'),
                         symbols=[dict(name=i.name.decode(errors='replace') if i.name else None,
                                       ordinal=i.ordinal, iat_va=hex(i.address)) for i in d.imports])
                    for d in getattr(pe, 'DIRECTORY_ENTRY_IMPORT', [])],
        'tls': str(pe.DIRECTORY_ENTRY_TLS.struct) if hasattr(pe, 'DIRECTORY_ENTRY_TLS') else None,
        'load_config': str(pe.DIRECTORY_ENTRY_LOAD_CONFIG.struct) if hasattr(pe, 'DIRECTORY_ENTRY_LOAD_CONFIG') else None,
        'runtime_function_count': len(getattr(pe, 'DIRECTORY_ENTRY_EXCEPTION', [])),
        'runtime_functions_sorted': runtime_starts == sorted(runtime_starts) if runtime_starts else None,
        'base_relocation_count': sum(len(block.entries) for block in getattr(pe, 'DIRECTORY_ENTRY_BASERELOC', [])),
        'resources': resources,
        'warnings': pe.get_warnings(),
    }
    args.out.mkdir(parents=True, exist_ok=False)
    (args.out / 'pe.json').write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding='utf-8')
    with (args.out / 'strings.txt').open('w', encoding='utf-8') as dest:
        for pattern, encoding in ((rb'[\x20-\x7e]{8,}', 'ascii'), (rb'(?:[\x20-\x7e]\x00){8,}', 'utf-16le')):
            for match in re.finditer(pattern, data):
                dest.write(f'{match.start():08x} {encoding} {match.group().decode(encoding)}\n')
    print(json.dumps({'report': str(args.out.resolve()), 'sha256': result['sha256'],
                      'imports': sum(len(d['symbols']) for d in result['imports'])}))


if __name__ == '__main__':
    main()
