#!/usr/bin/env python3
"""Inspect СТРУК routine boundaries using the existing disbesm6 field parser."""
from pathlib import Path
import runpy
ROOT = Path(__file__).resolve().parents[1]
parse = runpy.run_path(str(ROOT / 'tests/echolot-layout.py'))['parse_instructions']
NAMES = ('Fail','BindInput','BindOutput','FlushReport','Allocate','SkipComment',
         'SkipSpaces','ReadWord','Greater','SortRows','NextWord','NewLine',
         'PrintLine','PrintTable','SkipBody','ParseBlock','ReadAddress','ReadRequest')
ORIGINAL = tuple(int(v,8) for v in '166 204 216 231 250 267 322 346 434 466 537 604 613 635 1005 1025 1222 1302'.split())


def inspect(directory, label):
    ins = parse((directory / (label+'.lst')).read_text())
    helper = next(a for (a,h),op in ins.items() if h==0 and op==(0,0o37,3,False)
                  and ins.get((a,1))==(0,0o42,0o13,False)
                  and ins.get((a+1,0))==(0o17,0o44,0o13,False))
    main=ins[0o10,1][2]
    entries=[]
    for (a,h),op in ins.items():
        if a>=main: continue
        if ((h==0 and op==(0o14,0o31,helper,True))
            or (h==1 and op==(0o14,0o31,helper,True) and ins.get((a,0))==(0o17,0,3,False))
            or (h==0 and op==(0,0o43,0o13,False) and ins.get((a+1,0))==(0,0o37,3,False))):
            entries.append(a)
    return sorted(entries), main, helper, ins


def compare(directory):
    a,am,ah,ai=inspect(directory,'original'); b,bm,bh,bi=inspect(directory,'generated')
    assert tuple(a)==ORIGINAL
    assert len(b)==len(a),(len(a),len(b))
    rows=[]
    for name,x,y,xe,ye in zip(NAMES,a,b,a[1:]+[am],b[1:]+[bm]):
        rows.append(dict(name=name,original=f'{x:05o}',generated=f'{y:05o}',
                         original_words=f'{xe-x:04o}',generated_words=f'{ye-y:04o}',
                         size_match=xe-x==ye-y))
    return rows

if __name__=='__main__':
    import sys
    for row in compare(Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'build/struk-rebuild'):
        print(row)
