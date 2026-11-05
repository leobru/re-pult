#!/usr/bin/env python3
"""Inventory РЕЗРВ1/РЕЗРВ3 words and disassemble the ВЫЗОВЛ image."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]


def sha(data):return hashlib.sha256(data).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--disassembler',type=Path,default=ROOT.parent/'dispak-tools/disbesm6')
    args=parser.parse_args()
    out=ROOT/'build/pult-reserves';out.mkdir(parents=True,exist_ok=True)
    disks={v:Path('/usr/local/share/besm6')/v for v in ('2148','2248')}
    hashes={v:sha(p.read_bytes()) for v,p in disks.items()}
    rows=[];pages={}
    for v in disks:
        for name,start,count in (('РЕЗРВ1',0o1007,0o22),('РЕЗРВ3',0o1074,1)):
            target=out/f'{name}-{v}.bin';target.unlink(missing_ok=True)
            subprocess.run(['besmtool','dump',v,f'--start=0{start:o}',f'--length={count}',
                '--to-file='+str(target)],cwd='/usr/local/share/besm6',check=True,stdout=subprocess.DEVNULL)
            data=target.read_bytes();assert len(data)==6144*count
            for i in range(count):
                page=data[i*6144:(i+1)*6144];pages[v,start+i]=page
                words=[int.from_bytes(page[n:n+6],'big') for n in range(0,6144,6)]
                rows.append(dict(volume=v,reserve=name,zone=f'{start+i:04o}',
                    sha256=sha(page),nonzero_words=sum(bool(w) for w in words),
                    first_words=[f'{w:016o}' for w in words[:7]]))
    differences={}
    for z in [*range(0o1007,0o1031),0o1074]:
        a,b=pages['2148',z],pages['2248',z]
        differences[f'{z:04o}']=sum(a[i:i+6]!=b[i:i+6] for i in range(0,6144,6))
    assert [differences[f'{z:04o}'] for z in range(0o1007,0o1014)]==[1024,1024,1024,1024,1022]
    assert all(differences[f'{z:04o}']==0 for z in [*range(0o1014,0o1031),0o1074])
    most=pages['2148',0o1010]+pages['2148',0o1011]
    # Independent identification recorded by bega-re's JINN inventory.
    assert sha(most)=='7e99e93eafdc3f5b9c593e12366a2a1d84f2990533410135e07a953aad7bf7a9'
    assert pages['2148',0o1074]==pages['2248',0o1074]
    binary=out/'ВЫЗОВЛ.bin';binary.write_bytes(pages['2248',0o1074])
    r=subprocess.run([str(args.disassembler),'-b','-a0','-e237','-n',
        str(ROOT/'syms/ВЫЗОВЛ.sym'),str(binary)],capture_output=True,text=True,check=True)
    assert not r.stderr,r.stderr
    (out/'ВЫЗОВЛ.lst').write_text(r.stdout.replace('Code: 6144 (02000) words',
                                                'Code: 1024 (02000) words; 6144 bytes'))
    for v,p in disks.items():assert sha(p.read_bytes())==hashes[v],v
    report=dict(zones=rows,differing_words=differences,most_sha256=sha(most),
        vyzovl_sha256=sha(binary.read_bytes()),source_disks_sha256=hashes,source_disks_unchanged=True)
    (out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('РЕЗРВ1: only 1007–1013 differ; 1014–1030 identical')
    print('МОСТ: JINN inventory SHA-256 matched; ВЫЗОВЛ: both copies identical, disassembled')


if __name__=='__main__':main()
