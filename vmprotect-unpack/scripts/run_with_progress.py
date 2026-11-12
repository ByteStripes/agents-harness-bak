"""Run vmp-lazy-unpack with append-only observational progress, without full diagnostics."""
import argparse
import json
import sys
import time
from pathlib import Path


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tool-root',type=Path,required=True)
    parser.add_argument('--progress-log',type=Path,required=True)
    parser.add_argument('unpack_args',nargs=argparse.REMAINDER)
    args=parser.parse_args()
    root=args.tool_root.resolve(strict=True)
    if not (root/'unpack'/'tracer.py').is_file(): parser.error('Expected vmp-lazy-unpack source root')
    forwarded=args.unpack_args
    if forwarded and forwarded[0]=='--': forwarded=forwarded[1:]
    if not forwarded: parser.error('Provide unpack arguments after --')
    args.progress_log.parent.mkdir(parents=True,exist_ok=True)
    # Refuse accidental overwrites of an earlier run's evidence.
    with args.progress_log.open('x',encoding='utf-8') as stream:
        stream.write(json.dumps({'kind':'observer_start','arguments':forwarded})+'\n')
    sys.path.insert(0,str(root))
    from unpack import tracer
    original=tracer.Tracer.on_block
    started=time.monotonic()
    last=0
    def observed(self,uc,address,size,user_data):
        nonlocal last
        original(self,uc,address,size,user_data)
        if self.blocks % 65536 == 0 and time.monotonic()-last >= 5:
            last=time.monotonic()
            state={'elapsed_seconds':round(last-started,3),'bits':self.arch.bits,
                   'blocks':self.blocks,'address':hex(address),
                   'written_pages':len(self.written_destination_pages),
                   'resolved_import_writes':self.resolved_write_count,
                   'registers':tracer.register_state(uc,self.arch),'recent_events':self.events[-2:]}
            with args.progress_log.open('a',encoding='utf-8') as stream:
                stream.write(json.dumps(tracer.format_report(state))+'\n')
    tracer.Tracer.on_block=observed
    sys.argv=['unpack',*forwarded]
    tracer.main()


if __name__=='__main__':
    main()
