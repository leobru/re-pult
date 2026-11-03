#!/usr/bin/env python3
"""Probe exact REAL words near the largest magnitudes on private volumes."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import runpy
import shutil
import subprocess
import tempfile
from decimal import localcontext

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dispak',default='dispak')
    args=parser.parse_args()
    app=Path(shutil.which(args.dispak) or args.dispak).resolve()
    out=ROOT/'build/adsis-real-limits';out.mkdir(parents=True,exist_ok=True)
    spec=importlib.util.spec_from_file_location('segments',ROOT/'tests/pascal-segments.py')
    helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
    reference=runpy.run_path(str(ROOT/'tests/adsis-real-output.py'))
    template=(ROOT/'tests/adsis/real-limit.pas').read_text()
    volumes=ROOT/'build/volumes'
    hashes={v:hashlib.sha256((volumes/v).read_bytes()).hexdigest()
            for v in ('2148','2248','2068')}
    adsis=(ROOT/'images/2248/АДСИС.bin').read_bytes()
    for v,z in (('2148',0o1006),('2248',0o1006),('2068',0o6)):
        payload=b''.join(w.to_bytes(6,'big') for w in helper.raw_words((volumes/v).read_bytes(),z))
        assert payload==adsis,'runtime differs from the original АДСИС'
    results=[]
    with tempfile.TemporaryDirectory(prefix='pult-real-limits-') as temporary:
        p=Path(temporary)
        for v in hashes:shutil.copyfile(volumes/v,p/v)
        archive=p/'2345';archive.write_bytes(bytes((0o600+4)*helper.ZONE))
        job=p/'job.b6';job.write_text((ROOT/'pult2068.b6').read_text().replace(
            'лент 30(1С)^','лент 30(1С)^\nлент 50(2345-зп)^'))
        env=dict(os.environ,HOME=str(p))
        env.pop('BESM6_PATH',None);env.pop('BESM6_SMALL_DISKS',None)

        def session(name,commands):
            r=subprocess.run([str(app),'--725','--path='+str(p)+':/usr/local/share/besm6',
                '-p','-t','-t',str(job)],input=commands,text=True,capture_output=True,
                cwd=p,env=env,timeout=30)
            for suffix,text in (('input',commands),('out',r.stdout),('trace',r.stderr)):
                (out/(name+'.'+suffix)).write_text(text)
            assert r.returncode==0,(name,r.stdout,r.stderr[-2000:])
            return r

        r=session('archive','дай новарх 50 100 вася\nарх вася,50,100,400\nз тест(30)\nконец\n')
        assert 'МСВ   ТЕСТ' in r.stdout,r.stdout
        cases=[]
        for delta in (1,2,16,1024):
            for sign in (1,-1):
                mantissa=sign*((1<<40)-delta)
                word=(127<<41)|(mantissa&((1<<41)-1))
                cases.append((f"{'positive' if sign>0 else 'negative'}-{delta}",word))
        cases.append(('negative-minimum',(127<<41)|(1<<40)))
        cases.append(('negative-minimum-text',(127<<41)|(1<<40)))
        for name,word in cases:
            source=template.replace('@WORD@',f'{word:016o}')
            if name.endswith('-text'):
                source=source.replace(
                    "WRITELN('[',D:0,'][',X:26:D,']');\n        WRITELN(T,'[',D:0,'][',X:26:D,']')",
                    "WRITELN(T,'[',D:0,'][',X:26:D,']');\n        WRITELN('[',D:0,'][',X:26:D,']')")
            (out/(name+'.pas')).write_text(source)
            helper.write_words(archive,0o101,helper.gost_source(source))
            r=session(name,'арх вася,50,100\nпас тест - па\nконец\n')
            entries=[int(m[1],8) for m in re.finditer(
                r'^75474: ntr .* acc=([0-7]{16})',r.stderr,re.MULTILINE)]
            assert entries and set(entries)=={word},(name,entries,r.stdout)
            with localcontext() as context:
                context.prec=100
                value=reference['real_value'](word)
                rows=[re.findall(r'\[([^]]*)\]',line)
                      for line in r.stdout.splitlines() if line.startswith('[')]
                mismatches=[]
                for i,row in enumerate(rows):
                    precision=i%10+1
                    expected=reference['scientific'](value,precision).rjust(27)
                    if row!=[str(precision),expected]:
                        mismatches.append(dict(index=i,actual=row,expected=expected))
                item=dict(name=name,word=f'{word:016o}',value=str(value),
                    calls=len(entries),rows=len(rows),mismatches=mismatches,
                    avost='АВОСТ' in r.stdout,completed='ПРЕДЕЛ ПРОВЕРЕН' in r.stdout)
                if name.startswith('negative-minimum'):
                    assert item['avost'] and not item['completed'],item
                    assert len(entries)==1 and not rows,item
                    assert 'АВОСТ 000017' in r.stdout and '75521:' in r.stdout,r.stdout
                    assert '75521: avx 74043' in r.stderr,r.stderr[-3000:]
                    entry='74076' if name.endswith('-text') else '74105'
                    assert re.search(r'^'+entry+r': vtm',r.stderr,re.MULTILINE),entry
                else:
                    assert item['completed'] and not item['avost'],item
                    assert len(entries)==20 and len(rows)==20 and not mismatches,item
                    assert rows[:10]==rows[10:],item
                    assert 'ВСЕ СДЕЛАНО.' in r.stdout,r.stdout
                results.append(item)
                print(json.dumps(item,ensure_ascii=False),flush=True)
    for v,digest in hashes.items():
        assert hashlib.sha256((volumes/v).read_bytes()).hexdigest()==digest
    (out/'report.json').write_text(json.dumps(dict(results=results,
        source_volumes_sha256=hashes,source_volumes_unchanged=True),ensure_ascii=False,indent=2)+'\n')
    print('160 conversions matched; -2^63 failed at 75521 in both channels; source volumes unchanged')


if __name__=='__main__':main()
