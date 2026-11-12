"""Optional PE32 VirtualQuery/RtlUnwind models and selective observation hooks."""
import argparse
import importlib
import json
import sys
from pathlib import Path


def virtual_query32(self,symbol,address,output,length,unused):
    if address>=self.arch.user_top or length<28:
        self.last_error=87
        return 0,{'compat_model':'virtual_query32','invalid_range_or_length':True}
    if not output or not self.writable_range(output,28):
        self.last_error=998
        return 0,{'compat_model':'virtual_query32','invalid_output':True}
    info=self.memory_basic_information(address)
    if info is None or len(info)!=28: raise ValueError('Expected MEMORY_BASIC_INFORMATION32')
    self.uc.mem_write(output,info)
    return 28,{'compat_model':'virtual_query32','query_address':hex(address)}


def install_models():
    api=importlib.import_module('unpack.32bit.api_handlers_32').ApiHandlers32
    api._handlers.setdefault('virtualquery',(virtual_query32,3))
    cls=importlib.import_module('unpack.32bit.tracer_32').Tracer32
    original=cls.on_block
    def block(self,uc,address,size,user_data):
        label=self.synthetic_import_targets.get(address,'').lower()
        if self.single_step.active and label=='kernel32.dll!rtlunwind':
            self.blocks+=1
            self.add_event('rtlunwind_forwarded_alias',address,import_name=label)
            self.single_step.unwind()
            return
        original(self,uc,address,size,user_data)
    cls.on_block=block


def install_legacy_user32():
    from run_with_winstation import get_station,get_information,check_remote_debugger
    api=importlib.import_module('unpack.32bit.api_handlers_32').ApiHandlers32
    for name,handler,count in [('getprocesswindowstation',get_station,0),
                               ('getuserobjectinformationa',get_information,5),
                               ('getuserobjectinformationw',get_information,5),
                               ('checkremotedebuggerpresent',check_remote_debugger,2)]:
        api._handlers.setdefault(name,(handler,count))
    def message(self,symbol,window,text,caption,flags):
        return None,{'guest_message_text':self.read_utf16(text),'guest_message_caption':self.read_utf16(caption),'message_flags':flags}
    api._handlers.setdefault('messageboxw',(message,4))


def install_selective_hooks(tracer):
    from unicorn import UC_HOOK_BLOCK
    from unpack.hooks import TraceHooks
    class SelectiveHooks(TraceHooks):
        def __init__(self,t,peb,page):
            if t.arch.bits!=32 or t.diagnostics is not None:
                raise ValueError('Selective observation requires x86 without diagnostics')
            super().__init__(t,peb,page,native=False)
            self.uc.hook_del(self.handles.pop(0))
            ranges=[(1,t.image_start-1),(t.image_end,0xffffffffffffffff)]
            ranges += [(a,b-1) for a,b,_ in t.packed_destination_ranges]
            points={t.entry_address}|set(t.discovered_crc_loops)|set(t.decompressors.candidates)|set(t.stack_copy_candidates)
            points |= {a for a in t.synthetic_import_targets if t.in_module(a)}
            ranges += [(a,a) for a in points]
            merged=[]
            for a,b in sorted(ranges):
                if merged and a<=merged[-1][1]+1: merged[-1]=(merged[-1][0],max(b,merged[-1][1]))
                else: merged.append((a,b))
            for a,b in merged:
                self.handles.append(self.uc.hook_add(UC_HOOK_BLOCK,t.on_block,begin=a,end=b))
            self.backend='python-selective-callbacks-not-total-blocks'
    tracer.TraceHooks=SelectiveHooks


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tool-root',required=True,type=Path)
    parser.add_argument('--selective-hooks',action='store_true',help='Experimental opt-in; counters are callbacks, not all blocks')
    parser.add_argument('--legacy-user32',action='store_true',help='Opt-in legacy window-station models; MessageBox remains a stop')
    parser.add_argument('--ntdll-resources',action='store_true',help='Copy version resource from matching bundled ntdll')
    parser.add_argument('--dump-on-failure',type=Path,help='New path for partial memory PE; not a runnable artifact')
    parser.add_argument('--import-evidence',type=Path,help='New JSON path recording import provenance before reconstruction')
    parser.add_argument('unpack_args',nargs=argparse.REMAINDER)
    args=parser.parse_args()
    root=args.tool_root.resolve(strict=True)
    if not (root/'unpack'/'tracer.py').is_file(): parser.error('Expected vmp-lazy-unpack source root')
    forwarded=args.unpack_args
    if forwarded and forwarded[0]=='--': forwarded=forwarded[1:]
    if '--32bit' not in forwarded: parser.error('This adapter requires explicit --32bit')
    if args.selective_hooks and '--diagnostics' in forwarded:
        parser.error('Use ordinary hooks with full diagnostics')
    if args.dump_on_failure and args.dump_on_failure.exists(): parser.error('Failure dump path already exists')
    if args.import_evidence and args.import_evidence.exists(): parser.error('Import evidence path already exists')
    sys.path.insert(0,str(root))
    from unpack import tracer
    if args.import_evidence:
        original_report=tracer.build_resolved_import_report
        def capture(*values,**options):
            report=original_report(*values,**options)
            args.import_evidence.parent.mkdir(parents=True,exist_ok=True)
            with args.import_evidence.open('x',encoding='utf-8') as stream:
                json.dump(tracer.format_report(report),stream,indent=2)
            return report
        tracer.build_resolved_import_report=capture
    install_models()
    if args.legacy_user32: install_legacy_user32()
    if args.ntdll_resources:
        from run_with_winstation import install_ntdll_resources
        install_ntdll_resources(tracer)
    if args.selective_hooks: install_selective_hooks(tracer)
    if args.dump_on_failure:
        from unpack.dump import dump_pe
        original_stop=tracer.Tracer.stop_event
        def stop(self,event):
            try:
                if event.kind!='emulation_reached_unpacked_entry':
                    args.dump_on_failure.parent.mkdir(parents=True,exist_ok=True)
                    args.dump_on_failure.write_bytes(dump_pe(self.uc.mem_read,self.image_start))
            finally:
                original_stop(self,event)
        tracer.Tracer.stop_event=stop
    sys.argv=['unpack',*forwarded]
    tracer.main()


if __name__=='__main__':
    main()
