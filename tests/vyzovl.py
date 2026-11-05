#!/usr/bin/env python3
"""Recompile ВЫЗОВЛ on disposable disks and compare all 294 program words.

Only two known compiler-generated ADSIS targets may differ. --exact also
rejects those two words. No generated word is patched or masked.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import runpy
import shutil
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from gost import G, text
from make2068 import ZONE, payload, control_words, build


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dispak',default='dispak')
    parser.add_argument('--compiler',choices=['may','december'],default='may')
    parser.add_argument('--allow-differences',action='store_true')
    parser.add_argument('--exact',action='store_true')
    parser.add_argument('--compile-only',action='store_true')
    args=parser.parse_args()
    helper=runpy.run_path(str(ROOT/'tests/pascal-segments.py'))
    common=runpy.run_path(str(ROOT/'tests/rebuild-analyzers.py'))
    encode=runpy.run_path(str(ROOT/'tests/servic.py'))['encode_source']
    raw,install=common['raw_zones'],common['install_image']
    app=shutil.which(args.dispak)
    assert app,args.dispak
    volumes=ROOT/'build/volumes'
    disks={v:(volumes/v).read_bytes() for v in ('2148','2248','2068')}
    original=raw(disks['2148'],0o1074,1)
    assert original==raw(disks['2248'],0o1074,1)
    adsis=raw(disks['2068'],6,1)
    assert int.from_bytes(adsis[0o27*6:0o30*6],'big') >> 24 == 0o03074251
    assert int.from_bytes(adsis[0o32*6:0o33*6],'big') >> 24 == 0o03074313
    end=int.from_bytes(original[30:36],'big')
    assert end==0o446
    source=ROOT/'pascal/vyzovl.pas'
    out=ROOT/('build/vyzovl-rebuild'+('-december' if args.compiler=='december' else ''))
    out.mkdir(parents=True,exist_ok=True)
    date=out/'compile-date.c'
    date.write_text('#include <time.h>\nstruct tm *localtime(const time_t *v) {\n'
                    ' static _Thread_local struct tm d; (void)v;\n'
                    ' d=(struct tm){.tm_year=86,.tm_mon=6,.tm_mday=3,\n'
                    ' .tm_wday=4,.tm_yday=183}; return &d; }\n')
    library=out/'compile-date.so'
    subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror','-shared','-fPIC',
                    '-o',str(library),str(date)],check=True)
    compiler=disks['2248']
    if args.compiler=='december':
        compiler,_=build(volumes/'2148',volumes/'2248',
                         json.loads((ROOT/'tools/volume2068.json').read_text()))
    with tempfile.TemporaryDirectory(prefix='pult-vyzovl-') as directory:
        private=Path(directory)
        image=bytearray(disks['2068'])
        for z in range(0o101,0o115):
            data=payload(compiler,z if args.compiler=='december' else z+0o1000)
            start=(z+4)*ZONE
            image[start:start+ZONE]=control_words(z,data)+data
        (private/'2068').write_bytes(image)
        (private/'2248').write_bytes(disks['2248'])
        archive=private/'2345'
        archive.write_bytes(bytes((0o400+4)*ZONE))
        gost=lambda s:int.from_bytes(bytes(G.index(c) for c in s.ljust(6)),'big')
        catalog=[0]*1024
        catalog[:3]=[gost('ВАСЯ'),gost('ПРОБА'),(1<<24)|0o30]
        catalog[3:5]=[gost('ТЕКСТ'),(0o40<<24)|1]
        catalog[0o377]=5
        helper['write_words'](archive,0o100,catalog)
        helper['write_words'](archive,0o101,encode(source.read_text(),helper))
        helper['write_words'](archive,0o140,helper['gost_source']('(CAR\n (QUOTE (A B)))\n'))
        lisp=private/'2346'
        lisp.write_bytes(bytes((0o2000+4)*ZONE))
        helper['write_words'](lisp,0o1653,[0]*1024)
        job=private/'job.b6'
        job.write_text((ROOT/'pult2068.b6').read_text().replace(
            'лент 30(1С)^','лент 30(1С)^\nлент 50(2345-зп)^\nлент 66(2346)^'))
        env=dict(os.environ,DISPAK=app,LD_PRELOAD=str(library))
        env.pop('BESM6_PATH',None)
        env.pop('BESM6_SMALL_DISKS',None)

        def session(label,commands):
            (out/(label+'.input')).write_text(commands)
            result=subprocess.run([str(ROOT/'tools/run-dispak.sh'),'--725',
                '--path='+directory+':/usr/local/share/besm6','-p','-t',str(job)],
                input=commands,text=True,capture_output=True,cwd=private,env=env,timeout=60)
            (out/(label+'.out')).write_text(result.stdout)
            (out/(label+'.trace')).write_text(result.stderr)
            assert result.returncode==0 and 'АВОСТ' not in result.stdout,result.stdout
            return result.stdout

        result=session('compile','арх вася,50,100\nпас проба - па зонгп 500300 1\nконец\n')
        assert 'ВСЕ СДЕЛАНО.' in result and 'БЫЛИ ОШИБКИ' not in result and '***ОШ.' not in result,result
        date='09.12.88' if args.compiler=='december' else '17.05.88'
        assert 'ПАСКАЛЬ-АВТОКОД 9.('+date+')' in result,result
        generated=raw(archive.read_bytes(),0o300,1)
        newend=int.from_bytes(generated[30:36],'big')
        for label,data in [('original',original),('generated',generated)]:
            binary=out/(label+'.bin');binary.write_bytes(data)
            entries=out/(label+'.entries')
            stop=int.from_bytes(data[30:36],'big')
            entries.write_text(''.join(f'{i:05o}:\n' for i in range(0o102,stop)))
            dis=subprocess.run([str(ROOT.parent/'dispak-tools/disbesm6'),'-b','-a0','-e7',
                                '--trace='+str(entries),str(binary)],
                               capture_output=True,text=True,check=True)
            assert not dis.stderr,dis.stderr
            (out/(label+'.lst')).write_text(dis.stdout)
            (out/(label+'-literals.txt')).write_text(''.join(
                f'{a:05o} {data[a*6:(a+1)*6].hex().upper()} {text(data[a*6:(a+1)*6])}\n'
                for a in range(0o11,0o102)))
        differences=[f'{a:05o}' for a in range(max(end,newend))
                     if original[a*6:(a+1)*6]!=generated[a*6:(a+1)*6]]
        report=dict(source_sha256=sha(source.read_bytes()),compiler='Pascal-autocode 9 '+date,
                    compiler_sha256=sha(raw(compiler,0o101 if args.compiler=='december' else 0o1101,0o14)),
                    adsis_sha256=sha(adsis),
                    compilation_date='03.07.86',original_end=f'{end:05o}',generated_end=f'{newend:05o}',
                    compared_words=max(end,newend),differing_words=differences,
                    original_program_sha256=sha(original[:end*6]),
                    generated_program_sha256=sha(generated[:newend*6]),
                    literal_pool_exact=original[0o11*6:0o102*6]==generated[0o11*6:0o102*6],
                    exact_match=original[:end*6]==generated[:newend*6],
                    residual_words=1024-end,source_disks_sha256={v:sha(d) for v,d in disks.items()})
        report['differing_residual_words']=sum(original[a*6:(a+1)*6]!=generated[a*6:(a+1)*6]
                                               for a in range(end,1024))
        (out/'comparison.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
        print('ВЫЗОВЛ:',report['original_end'],'→',report['generated_end'],
              'differences',len(differences),'literal pool exact',report['literal_pool_exact'],flush=True)
        known={0o443:(0o0444001367174027,0o0444001367174251),
               0o445:(0o6044001603074032,0o6044001603074313)}
        if not args.allow_differences:
            assert newend==end and set(differences)=={'00443','00445'},'see '+str(out/'comparison.json')
            for a,(before,after) in known.items():
                assert int.from_bytes(original[a*6:(a+1)*6],'big')==before
                assert int.from_bytes(generated[a*6:(a+1)*6],'big')==after
        report['compiler_differences']={f'{a:05o}':dict(original=f'{v[0]:016o}',
                                                     generated=f'{v[1]:016o}')
                                        for a,v in known.items()}
        regions=[('header',0,0o11),('literals',0o11,0o102),
                 ('SkipSpaces',0o102,0o110),('ReadName',0o110,0o157),
                 ('GetArchive',0o157,0o200),('BindInput',0o200,0o212),
                 ('BindOutput',0o212,0o225),('FlushOutput',0o225,0o237),
                 ('main',0o237,0o417),('templates',0o417,0o435),
                 ('procedure-prologue',0o435,0o441),('program-initializer',0o441,0o446)]
        report['regions']=[dict(name=n,start=f'{a:05o}',end=f'{b:05o}',words=b-a,
                                exact_match=original[a*6:b*6]==generated[a*6:b*6]) for n,a,b in regions]
        if args.exact:
            assert not differences,'two compiler-generated ADSIS calls differ; see comparison.json'
        if not args.compile_only:
            cases={
                'missing-name':('лес\nконец\n','ГДЕ ЖЕ ИМЯ ?'),
                'no-archive':('лес тест\nконец\n','НЕТ НАСТРОЙКИ НА АРХИВ'),
                'missing-file':('арх вася,50,100\nлес нет\nконец\n','НЕТ ИМЕНИ'),
                'translator-signature':('арх вася,50,100\nлес текст\nконец\n',
                                        'ИСПОРЧЕН ЛИСП-ТРАНСЛЯТОР'),
            }
            for case,(commands,expected) in cases.items():
                results=[]
                archive_before=archive.read_bytes()
                for label,data in [('original',original),('generated',generated)]:
                    (private/'2068').write_bytes(image)
                    # ЛЕС uses the ordinary Pascal launcher, which prepares
                    # the outer frame needed by EXIT. This is a probe alias.
                    install(private/'2068',0o55,3,data)
                    output=session(case+'-'+label,commands)
                    assert expected in output,output
                    assert 'КОНЕЦ ЗАДАЧИ' in output,output
                    assert archive.read_bytes()==archive_before,case+' changed the source archive'
                    results.append(output.split('ВРЕМЯ РЕШ:',1)[0])
                assert results[0]==results[1],case
            report['functional_cases']=list(cases)
            report['probe_launcher']='ЛЕС slot, private 2068:055–057; ordinary Pascal outer frame'
            report['signature_fixture']='private unit 66, zero signature at 1653:1252'
    assert all((volumes/v).read_bytes()==data for v,data in disks.items())
    report['source_volumes_unchanged']=True
    (out/'comparison.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('ВЫЗОВЛ: checked compiler targets, procedure regions and',
          len(report.get('functional_cases',[])), 'behavior cases; source volumes unchanged')


if __name__=='__main__':
    main()
