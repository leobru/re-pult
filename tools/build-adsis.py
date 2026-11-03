#!/usr/bin/env python3
"""Assemble adsis.be and compare the complete ЗОНГП zone with 2148/2248."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build/adsis-asm'
HEADER='''шифр 419999^
трак 64^
лент 30(2048-6200)^
лент 42(2099)^
лент 43(1234-ЗП)^
ацп 40^
росп 0^
врем 240^
лист 0-37^
вход 4000^
е
в 4000
к 00 010 4003
к 15 24 04000
к 00 066 0001 00 000 0100
с 3000 67
в 14000
а1
ВВД$$$^
'''
TAIL='''КВЧ$$$^
ТРН$$$^
0-0^
ЧТКОМП420070^
НАЗ   074000^
ЗОНГП 430001  000001^
КНЦ$$$^
_$ЕКОНЕЦ
'''


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dispak',default=os.environ.get('DISPAK','dispak'))
    args=parser.parse_args()
    app=Path(shutil.which(args.dispak) or args.dispak).resolve()
    source=(ROOT/'adsis.be').read_text()
    for n,line in enumerate(source.splitlines(),1):
        assert len(line)<=72,f'adsis.be:{n}: card exceeds 72 columns'
        if line and not line[0].isspace() and not line.startswith('*'):
            assert len(line.split()[0])<=6,f'adsis.be:{n}: label exceeds six characters'
    OUT.mkdir(parents=True,exist_ok=True)
    home=OUT/'home';(home/'.besm6').mkdir(parents=True,exist_ok=True)
    env=dict(os.environ,HOME=str(home),BESM6_PATH=str(OUT)+':/usr/local/share/besm6')
    env.pop('BESM6_SMALL_DISKS',None)
    originals={}
    disks={v:Path('/usr/local/share/besm6')/v for v in ('2048','2099','2148','2248')}
    hashes={v:hashlib.sha256(p.read_bytes()).hexdigest() for v,p in disks.items()}
    for v in ('2148','2248'):
        target=OUT/(v+'-01006.bin');target.unlink(missing_ok=True)
        subprocess.run(['besmtool','dump',v,'--start=01006','--length=1',
            '--to-file='+str(target)],cwd=OUT,env=env,check=True,stdout=subprocess.DEVNULL)
        originals[v]=target.read_bytes()
        assert originals[v]==(ROOT/'images'/v/'АДСИС.bin').read_bytes(),v
    assert len(originals['2248'])==6144 and originals['2148']==originals['2248']
    (OUT/'1234').write_bytes(b'')
    deck=OUT/'adsis.b6';deck.write_text(HEADER+''.join(l+'^\n' for l in source.splitlines())+TAIL)
    listing=OUT/'adsis.lst'
    with listing.open('w') as stream:
        result=subprocess.run([str(app),'--path='+env['BESM6_PATH'],'-l',str(deck)],
            cwd=OUT,env=env,stdin=subprocess.DEVNULL,stdout=stream,stderr=subprocess.STDOUT,timeout=60)
    text=listing.read_text(encoding='utf-8-sig').translate(str.maketrans('ABCEHKMOPTXY','АВСЕНКМОРТХУ'))
    errors=[int(n) for n in re.findall(r'ОШИБОК\s*=\s*(\d+)',text)]
    assert result.returncode==0 and errors and not any(errors),'BEMSH errors: '+str(listing)
    assert 'МАКС СЕРЬЕЗН=0.' in text and 'АВОСТ' not in text,str(listing)
    assert re.search(r'ЗОНГП\s*=\s*430001\s+СВ\.ЗОНА\s*=\s*430002\s+'
                     r'АМИН=74000\s+АМАКС=75777\s+АСВОБ=76000',text),str(listing)
    assert 'КОНЕЦ ЗАДАЧИ' in text,str(listing)
    rebuilt=OUT/'adsis.img';rebuilt.unlink(missing_ok=True)
    subprocess.run(['besmtool','dump','1234','--start=01','--length=1',
        '--to-file='+str(rebuilt)],cwd=OUT,env=env,check=True,stdout=subprocess.DEVNULL)
    old,new=originals['2248'],rebuilt.read_bytes()
    assert len(new)==6144,'ЗОНГП did not produce a full zone'
    differences=[dict(address=f'{0o74000+i//6:05o}',
        original=f'{int.from_bytes(old[i:i+6],"big"):016o}',
        rebuilt=f'{int.from_bytes(new[i:i+6],"big"):016o}')
        for i in range(0,6144,6) if old[i:i+6]!=new[i:i+6]]
    for v,path in disks.items():assert hashlib.sha256(path.read_bytes()).hexdigest()==hashes[v],v
    report=dict(source_sha256=hashlib.sha256(source.encode()).hexdigest(),
        original_sha256=hashlib.sha256(old).hexdigest(),rebuilt_sha256=hashlib.sha256(new).hexdigest(),
        original_zones=['2148:01006','2248:01006'],bytes=6144,words=1024,
        identical_words=1024-len(differences),different_words=len(differences),
        different_bytes=sum(a!=b for a,b in zip(old,new)),differences=differences,
        bemsh_errors=errors,source_disks_sha256=hashes,source_disks_unchanged=True)
    (OUT/'comparison.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    assert not differences,f'{len(differences)} differing words; see {OUT}/comparison.json'
    print('BEMSH: zero errors; ЗОНГП 430001 000001, АМИН=74000 АМАКС=75777')
    print('1024/1024 words; 6144/6144 bytes identical to 2148:01006 and 2248:01006')
    print('SHA-256: '+report['rebuilt_sha256'])


if __name__=='__main__':main()
