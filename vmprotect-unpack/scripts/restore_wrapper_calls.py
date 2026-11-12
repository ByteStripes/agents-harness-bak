"""Conservatively restore original wrapper-call bytes using an exact reconstruction report."""
import argparse
import hashlib
import json
from pathlib import Path


def restore(data,report):
    output=bytearray(data)
    selected=[]
    occupied=set()
    for patch in report['patches']:
        if patch['category'] not in ('encoded_wrapper','api_wrapper'): continue
        raw_offset=patch['patch_file_offset']
        offset=int(raw_offset,0) if isinstance(raw_offset,str) else raw_offset
        old=bytes.fromhex(patch['old_bytes']);new=bytes.fromhex(patch['new_bytes'])
        if not old or len(old)!=len(new) or not 0<=offset<=len(data)-len(new):
            raise ValueError('Invalid equal-width wrapper patch')
        positions=set(range(offset,offset+len(new)))
        if occupied & positions: raise ValueError('Overlapping wrapper patches require manual review')
        if data[offset:offset+len(new)]!=new: raise ValueError(f'Patch preimage mismatch at {offset:#x}')
        occupied.update(positions)
        selected.append((offset,old))
    if not selected: raise ValueError('No wrapper patches selected; do not claim this fallback changed anything')
    for offset,old in selected: output[offset:offset+len(old)]=old
    return bytes(output),len(selected)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input',type=Path)
    parser.add_argument('--report',required=True,type=Path)
    parser.add_argument('--sha256',required=True,help='Expected hash of this exact input')
    parser.add_argument('--out',required=True,type=Path)
    args=parser.parse_args()
    data=args.input.read_bytes()
    if hashlib.sha256(data).hexdigest()!=args.sha256.lower(): parser.error('Input hash mismatch')
    if args.out.exists(): parser.error('Refusing to overwrite an existing output')
    output,count=restore(data,json.loads(args.report.read_text(encoding='utf-8')))
    args.out.parent.mkdir(parents=True,exist_ok=True)
    with args.out.open('xb') as stream: stream.write(output)
    print(json.dumps({'restored_wrapper_patches':count,'sha256':hashlib.sha256(output).hexdigest(),'output':str(args.out.resolve())}))


if __name__=='__main__': main()
