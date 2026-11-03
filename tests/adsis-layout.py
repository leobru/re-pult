#!/usr/bin/env python3
"""Audit the АДСИС page, its symbol map and executed instruction addresses.

Usage: python3 tests/adsis-layout.py [--traces build/adsis-probes]
Writes a reproducible address/coverage report; instruction fields come from
an existing disbesm6 parser. No image or source-volume bytes are changed.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import runpy
import subprocess

ROOT = Path(__file__).resolve().parents[1]
START, END = 0o74000, 0o76000
REGIONS = (
    ('vector', 0o74000, 0o74113),
    ('finish', 0o74113, 0o74136),
    ('integer-conversion', 0o74136, 0o74143),
    ('debug-and-constants', 0o74143, 0o74166),
    ('frame-return-and-pack', 0o74166, 0o74204),
    ('allocation', 0o74204, 0o74222),
    ('standard-streams', 0o74222, 0o74337),
    ('unpack-and-mod', 0o74337, 0o74362),
    ('files', 0o74362, 0o75075),
    ('heap-init', 0o75075, 0o75104),
    ('gost-itm', 0o75104, 0o75155),
    ('label-names', 0o75155, 0o75175),
    ('unused-fragment', 0o75175, 0o75201),
    ('shared-state', 0o75201, 0o75241),
    ('bounds-and-context', 0o75241, 0o75260),
    ('text-output', 0o75260, 0o75400),
    ('stack-unwind', 0o75400, 0o75424),
    ('integer-output', 0o75424, 0o75474),
    ('real-output', 0o75474, 0o75650),
    ('real-compare', 0o75650, 0o75675),
    ('terminal-input', 0o75675, 0o75714),
    ('frame-registers', 0o75714, 0o75730),
    ('sets', 0o75730, 0o75750),
    ('file-close', 0o75750, 0o75754),
    ('zone-tail', 0o75754, END),
)


def audit(traces=None, output=None):
    image = (ROOT / 'images/2248/АДСИС.bin').read_bytes()
    assert len(image) == 6144
    assert image == (ROOT / 'images/2148/АДСИС.bin').read_bytes()
    kinds, names = {}, {}
    for line in (ROOT / 'syms/АДСИС.sym').read_text().splitlines():
        fields = line.split()
        if not fields:
            continue
        span, typ, name = fields[:3]
        bounds = [int(a,8) for a in span.split('-')]
        lo, hi = bounds[0], bounds[-1]
        assert typ in ('B','C','A','D','G','H','I','J','K','L','M','N','R','T','257'), typ
        kind = 'code' if typ in ('B','C','A') else 'data'
        for address in range(max(lo,START),min(hi+1,END)):
            assert kinds.get(address,kind)==kind, f'conflicting symbol type at {address:05o}'
            kinds[address]=kind
            if name != '-':
                names.setdefault(address,[]).append(name)
    assert set(kinds)==set(range(START,END)), 'unclassified АДСИС words'
    listing = subprocess.run([str(ROOT.parent / 'dispak-tools/disbesm6'), '-b',
        '-a74000', '-e74003', '-n', str(ROOT / 'syms/АДСИС.sym'),
        str(ROOT / 'images/2248/АДСИС.bin')], capture_output=True,text=True,check=True).stdout
    parse = runpy.run_path(str(ROOT / 'tests/echolot-layout.py'))['parse_instructions']
    instructions=parse(listing)
    direct=[]
    for (address,half), (reg,op,target,long) in sorted(instructions.items()):
        if kinds.get(address)!='code' or not long:
            continue
        # VJM uses an absolute target regardless of its link register.
        if op==0o31 or (reg==0 and op in (0o26,0o27,0o30)):
            if START<=target<END:
                direct.append(dict(source=f'{address:05o}:{half}',target=f'{target:05o}'))
                assert kinds[target]=='code', f'direct branch into data: {address:05o} -> {target:05o}'
    executed=set(); by_trace={}
    if traces:
        for path in sorted(Path(traces).glob('*.trace')):
            addresses=set()
            with path.open() as stream:
                for line in stream:
                    match=re.match(r'^([0-7]{5})[:;] (?!store )',line)
                    if match and START<=int(match[1],8)<END:
                        addresses.add(int(match[1],8))
            bad=addresses-{a for a,kind in kinds.items() if kind=='code'}
            assert not bad, f'{path.name}: executed data words '+','.join(f'{a:05o}' for a in sorted(bad))
            by_trace[path.name]=dict(words=len(addresses),addresses=[f'{a:05o}' for a in sorted(addresses)])
            executed.update(addresses)
    regions=[]
    for name,lo,hi in REGIONS:
        code={a for a in range(lo,hi) if kinds[a]=='code'}
        regions.append(dict(name=name,start=f'{lo:05o}',end=f'{hi-1:05o}',
                            code_words=len(code),data_words=hi-lo-len(code),
                            executed_words=len(code&executed),
                            unexecuted_code=[f'{a:05o}' for a in sorted(code-executed)]))
    report=dict(sha256=hashlib.sha256(image).hexdigest(),words=1024,
                symbols={f'{a:05o}':list(dict.fromkeys(n)) for a,n in sorted(names.items())},
                code_words=sum(v=='code' for v in kinds.values()),
                data_words=sum(v=='data' for v in kinds.values()),
                executed_words=len(executed),executed_data_words=[],
                direct_transfers=direct,regions=regions,traces=by_trace)
    if output:
        output=Path(output); output.parent.mkdir(parents=True,exist_ok=True)
        output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(f"АДСИС: {report['code_words']} code words, {report['data_words']} data words; "
          f"{len(direct)} direct transfers into code; {len(executed)} executed words")
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--traces',type=Path)
    parser.add_argument('--output',type=Path,default=ROOT/'build/АДСИС-map.json')
    args=parser.parse_args()
    audit(args.traces,args.output)
