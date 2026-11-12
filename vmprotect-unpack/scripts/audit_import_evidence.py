"""Read-only audit of scan-only additional imports. Flags candidates; never deletes imports."""
import argparse,json,struct
from pathlib import Path


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pe',type=Path)
    parser.add_argument('--evidence',required=True,type=Path)
    parser.add_argument('--reconstruction',required=True,type=Path)
    parser.add_argument('--out',required=True,type=Path)
    args=parser.parse_args()
    import pefile
    evidence=json.loads(args.evidence.read_text(encoding='utf-8'))
    report=json.loads(args.reconstruction.read_text(encoding='utf-8'))
    pe=pefile.PE(data=args.pe.read_bytes());ptr=8 if pe.OPTIONAL_HEADER.Magic==0x20b else 4
    image=pe.get_memory_mapped_image();result=[]
    def key(r):return r['module'].lower(),r['symbol']
    for item in evidence['resolved_imports']:
        if item.get('source')!='final_scan_only':continue
        slot=int(item['slot_va'],0) if isinstance(item['slot_va'],str) else item['slot_va']
        references=image.count(struct.pack('<Q' if ptr==8 else '<I',slot))
        row={'module':item['module'],'symbol':item['symbol'],'slot_rva':item['slot_rva'],'section':item['section'],
             'bootstrap_evidence':sum(key(r)==key(item) for r in evidence['bootstrap_iat']),
             'encoded_metadata_evidence':sum(key(r)==key(item) for r in evidence['encoded_imports']),
             'instruction_patch_count':sum(key(r)==key(item) for r in report['patches']),
             'absolute_slot_reference_count':references,
             'status':'needs_manual_review','note':'Address equality alone is not proof of an API pointer; generated thunks are not independent evidence.'}
        result.append(row)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    with args.out.open('x',encoding='utf-8') as stream:json.dump(result,stream,indent=2)
    print(json.dumps({'scan_only_candidates':len(result),'report':str(args.out.resolve())}))


if __name__=='__main__':main()
