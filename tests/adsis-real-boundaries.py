#!/usr/bin/env python3
"""Check adjacent positive REAL words and sign mirrors around powers."""
import argparse
from decimal import Decimal, ROUND_HALF_UP, ROUND_FLOOR, localcontext
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

ROOT=Path(__file__).resolve().parents[1]
LOW=1<<39
HIGH=(1<<40)-1

# Checked deviations of the original library from exact decimal half-up.
ROUNDING_ERRORS={
    ('0650000000000000',10): '2.2204460492Е-16',
    ('1450000000000001',10): '9.0949470178Е-13',
    ('1750000000000001',10): '5.8207660913Е-11',
    ('2150000000000000',10): '9.3132257461Е-10',
    ('3050000000000000',10): '1.5258789062Е-05',
    ('3110000000000000',9): '3.051757812Е-05',
    ('3150000000000000',8): '6.10351562Е-05',
    ('3250000000000000',7): '2.4414062Е-04',
    ('3310000000000000',6): '4.882812Е-04',
    ('3350000000000000',5): '9.76562Е-04',
    ('3410000000000000',5): '1.95312Е-03',
    ('3450000000000000',4): '3.9062Е-03',
    ('3650000000000000',1): '6.2Е-02',
    ('7310000000000000',10): '9.0071992548Е+15',
}


def neighbor(word,step):
    exponent,mantissa=word>>41,word&((1<<41)-1)
    mantissa+=step
    if mantissa<LOW:exponent-=1;mantissa=HIGH
    if mantissa>HIGH:exponent+=1;mantissa=LOW
    return (exponent<<41)|mantissa if 0<=exponent<=127 else None


def nearest(value):
    exponent=0
    while value/Decimal(2)**exponent>=1:exponent+=1
    while value/Decimal(2)**exponent<Decimal('0.5'):exponent-=1
    mantissa=int((value*Decimal(2)**(40-exponent)).to_integral_value(rounding=ROUND_HALF_UP))
    if mantissa==1<<40:exponent+=1;mantissa=LOW
    assert -64<=exponent<=63
    return ((exponent+64)<<41)|mantissa


def negative(word):
    exponent,mantissa=word>>41,word&((1<<41)-1)
    if mantissa==LOW and exponent>0:exponent-=1;mantissa*=2
    return (exponent<<41)|((-mantissa)&((1<<41)-1))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dispak',default='dispak')
    parser.add_argument('--case-id',type=int,action='append',help='trace selected IDs from the full sweep')
    parser.add_argument('--log10-constant',type=Decimal,help='replace 75627 in the private 2068 copy only')
    args=parser.parse_args()
    app=Path(shutil.which(args.dispak) or args.dispak).resolve()
    out=ROOT/'build/adsis-real-boundaries';out.mkdir(parents=True,exist_ok=True)
    spec=importlib.util.spec_from_file_location('segments',ROOT/'tests/pascal-segments.py')
    helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
    ref=runpy.run_path(str(ROOT/'tests/adsis-real-output.py'))
    cases={}
    with localcontext() as ctx:
        ctx.prec=100
        for base,powers in ((10,range(-19,19)),(2,range(-65,63))):
            for power in powers:
                center=nearest(Decimal(base)**power)
                for side in (-1,0,1):
                    word=neighbor(center,side) if side else center
                    if word is None:continue
                    for sign in (1,-1):
                        bits=word if sign>0 else negative(word)
                        cases.setdefault(bits,[]).append(dict(base=base,power=power,
                            side=side,sign=sign))
    cases=[dict(id=i+1,word=f'{word:016o}',boundaries=boundaries)
           for i,(word,boundaries) in enumerate(cases.items())]
    known=dict(ROUNDING_ERRORS)
    for (word,digits),text in ROUNDING_ERRORS.items():
        known[(f'{negative(int(word,8)):016o}',digits)]='-'+text
    if args.case_id:
        cases=[c for c in cases if c['id'] in args.case_id]
        assert len(cases)==len(set(args.case_id)),args.case_id
        out=out/('cases-'+'-'.join(map(str,args.case_id)));out.mkdir(exist_ok=True)
    replacement=None
    if args.log10_constant is not None:
        with localcontext() as ctx:
            ctx.prec=100
            replacement=nearest(args.log10_constant)
        out=out/('log10-'+str(args.log10_constant));out.mkdir(exist_ok=True)
    volumes=ROOT/'build/volumes'
    hashes={v:hashlib.sha256((volumes/v).read_bytes()).hexdigest() for v in ('2148','2248','2068')}
    image=(ROOT/'images/2248/АДСИС.bin').read_bytes()
    for v,z in (('2148',0o1006),('2248',0o1006),('2068',0o6)):
        assert b''.join(w.to_bytes(6,'big') for w in helper.raw_words((volumes/v).read_bytes(),z))==image
    results=[]
    template=(ROOT/'tests/adsis/real-boundaries.pas').read_text()
    with tempfile.TemporaryDirectory(prefix='pult-real-boundaries-') as temp:
        private=Path(temp)
        for v in hashes:shutil.copyfile(volumes/v,private/v)
        if replacement is not None:
            location=(0o6+4)*helper.ZONE+64+(0o75627-0o74000)*8
            with (private/'2068').open('r+b') as stream:
                stream.seek(location);old=int.from_bytes(stream.read(8),'little')
                expected=int.from_bytes(image[(0o75627-0o74000)*6:][:6],'big')
                assert old&((1<<48)-1)==expected
                stream.seek(location)
                stream.write(((old&~((1<<48)-1))|replacement).to_bytes(8,'little'))
        archive=private/'2345';archive.write_bytes(bytes((0o600+4)*helper.ZONE))
        job=private/'job.b6';job.write_text((ROOT/'pult2068.b6').read_text().replace(
            'лент 30(1С)^','лент 30(1С)^\nлент 50(2345-зп)^'))
        env=dict(os.environ,HOME=str(private));env.pop('BESM6_PATH',None);env.pop('BESM6_SMALL_DISKS',None)

        def session(name,commands,trace=False):
            (out/(name+'.input')).write_text(commands)
            r=subprocess.run([str(app),'--725','--path='+str(private)+':/usr/local/share/besm6',
                '-p','-t',*(['-t'] if trace else []),str(job)],input=commands,text=True,
                capture_output=True,cwd=private,env=env,timeout=30)
            (out/(name+'.out')).write_text(r.stdout);(out/(name+'.trace')).write_text(r.stderr)
            assert r.returncode==0 and 'АВОСТ' not in r.stdout,(name,r.stdout,r.stderr[-2000:])
            return r

        r=session('archive','дай новарх 50 100 вася\nарх вася,50,100,400\nз тест(30)\nконец\n')
        assert 'МСВ   ТЕСТ' in r.stdout
        for start in range(0,len(cases),24):
            batch=cases[start:start+24];name=f'batch-{start//24:03d}'
            code=[]
            for i,case in enumerate(batch):
                code.extend([f"    I:={case['id']};",
                    f"    CODE(СЧR{i:03d}=ПБN{i:03d},С;R{i:03d}:{case['word']},К;N{i:03d}:);",
                    '    X:=; PRINT;'])
            source=template.replace('@CASES@','\n'.join(code))
            (out/(name+'.pas')).write_text(source)
            helper.write_words(archive,0o101,helper.gost_source(source))
            r=session(name,'арх вася,50,100\nпас тест - па\nконец\n',trace=start==0)
            assert 'ГРАНИЦЫ ПРОВЕРЕНЫ' in r.stdout and 'ВСЕ СДЕЛАНО.' in r.stdout,r.stdout
            rows=[re.findall(r'\[([^]]*)\]',line) for line in r.stdout.splitlines() if line.startswith('[')]
            count=len(batch)*10
            assert len(rows)==count*2,(name,len(rows),count*2)
            assert rows[:count]==rows[count:],(name,'OUTPUT/TEXT differ')
            if start==0:
                entries=[m[1] for m in re.finditer(r'^75474: ntr .* acc=([0-7]{16})',r.stderr,re.MULTILINE)]
                assert entries==[c['word'] for c in batch for unused in range(20)]
                if replacement is not None:
                    factors=re.findall(r'^75526: a\*x 75627\s+\(=([0-7]{16})\)',r.stderr,re.MULTILINE)
                    assert factors and set(factors)=={f'{replacement:016o}'},factors
            with localcontext() as ctx:
                ctx.prec=100
                for case in batch:
                    value=ref['real_value'](int(case['word'],8));case['value']=str(value)
                for channel,part in zip(('OUTPUT','TEXT'),(rows[:count],rows[count:])):
                    for n,row in enumerate(part):
                        case=batch[n//10];digits=n%10+1
                        assert row[:2]==[str(case['id']),str(digits)],(name,row)
                        wanted=ref['scientific'](Decimal(case['value']),digits)
                        actual=row[2].strip()
                        issue=None
                        if abs(Decimal(case['value']))<Decimal(2)**-60:
                            observed=('-' if Decimal(case['value'])<0 else '')+'0.'+'0'*digits+'Е+17'
                            issue='lost-small-value'
                        elif (case['word'],digits) in known:
                            observed=known[(case['word'],digits)];issue='rounding'
                        else:observed=wanted
                        if replacement is None:
                            assert actual==observed,(case,row,wanted,observed)
                        if actual==wanted:issue=None
                        elif issue is None:issue='new-rounding'
                        assert row[2]==actual.rjust(27),(case,row)
                        results.append(dict(id=case['id'],channel=channel,precision=digits,issue=issue,
                            expected=wanted,actual=actual,matched=actual==wanted,
                            field_width=len(row[2])))
            print(f'{name}: {len(batch)} words, {count*2} conversions',flush=True)
    for v,digest in hashes.items():assert hashlib.sha256((volumes/v).read_bytes()).hexdigest()==digest
    mismatches=[r for r in results if not r['matched']]
    lost=sum(r['issue']=='lost-small-value' for r in results)
    rounding=sum(r['issue']=='rounding' for r in results)
    if not args.case_id and replacement is None:
        assert (len(cases),len(results),lost,rounding)==(988,19760,720,56)
    report=dict(cases=cases,conversions=len(results),lost_small=lost,rounding_errors=rounding,
        mismatches=mismatches,results=results,
        source_volumes_sha256=hashes,source_volumes_unchanged=True)
    if replacement is not None:
        baseline=json.loads((ROOT/'build/adsis-real-boundaries/report.json').read_text())
        original={(r['id'],r['channel'],r['precision']):r for r in baseline['results']}
        changes=[r for r in results if any(r[k]!=original[(r['id'],r['channel'],r['precision'])][k]
                                         for k in ('actual','field_width'))]
        with localcontext() as ctx:
            ctx.prec=100
            old_value=ref['real_value'](expected)
            new_value=ref['real_value'](replacement)
            estimates=[dict(binary_exponent=e,
                old=int((Decimal(e)*old_value).to_integral_value(rounding=ROUND_FLOOR)),
                new=int((Decimal(e)*new_value).to_integral_value(rounding=ROUND_FLOOR)))
                for e in range(-64,64)]
        report['constant_patch']=dict(address='75627',old_word=f'{expected:016o}',
            new_word=f'{replacement:016o}',requested=str(args.log10_constant),
            stored=str(new_value),changed_conversions=changes,exponent_estimates=estimates)
        print(f'Constant patch: {expected:016o} -> {replacement:016o}; {len(changes)} changed conversions')
    (out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(f'{len(cases)} unique words; {len(results)} conversions; '
          f'{lost} lost small values, {rounding} rounding errors; all observed results verified')


if __name__=='__main__':main()
