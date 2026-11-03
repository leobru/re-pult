#!/usr/bin/env python3
"""Find resident-page variants on 2148/2248 and disassemble distinct images.

Search scores exclude zero words. Sparse shared routines remain candidates;
whole-page variants require 500 aligned nonzero or 200 distinctive words.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import runpy
import subprocess

ROOT=Path(__file__).resolve().parents[1]

REFERENCES={
    'АДСИС':(0o1006,0o74000,'АДСИС.sym'),
    'СБОЙ':(0o1035,0o76000,'СБОЙ.sym'),
    'ПУСК':(0o1040,0,'ПУСК.sym'),
    'НАБЛ':(0o1041,0o56000,'НАБЛ.sym'),
    'КСБRUN':(0o1117,0o76000,'КСБRUN.sym'),
}


def digest(data):return hashlib.sha256(data).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--disassembler',type=Path,default=ROOT.parent/'dispak-tools/disbesm6')
    args=parser.parse_args()
    out=ROOT/'build/pult-residents';out.mkdir(parents=True,exist_ok=True)
    disks={v:Path('/usr/local/share/besm6')/v for v in ('2148','2248')}
    hashes={v:digest(p.read_bytes()) for v,p in disks.items()}
    raw={};pages={};wordsets={}
    for v in disks:
        target=out/(v+'.bin');target.unlink(missing_ok=True)
        subprocess.run(['besmtool','dump',v,'--to-file='+str(target)],check=True,
                       cwd='/usr/local/share/besm6',stdout=subprocess.DEVNULL)
        raw[v]=target.read_bytes();assert len(raw[v])%6144==0
        words=[int.from_bytes(raw[v][i:i+6],'big') for i in range(0,len(raw[v]),6)]
        pages[v]=[words[i:i+1024] for i in range(0,len(words),1024)]
        wordsets[v]=[set(p)-{0} for p in pages[v]]
    frequency=Counter()
    for sets in wordsets.values():
        for s in sets:frequency.update(s)
    candidates=[];selected={}
    for family,(reference_zone,load,sym) in REFERENCES.items():
        ref=pages['2248'][reference_zone];counts=Counter(ref)
        distinctive={w for w in ref if w and counts[w]==1 and frequency[w]<=20}
        for v,zones in pages.items():
            for zone,words in enumerate(zones):
                shared=len(distinctive&wordsets[v][zone])
                if shared<20:continue
                aligned=sum(a==b and a!=0 for a,b in zip(ref,words))
                union=sum(bool(a or b) for a,b in zip(ref,words))
                whole=aligned>=500 or shared>=200
                row=dict(family=family,volume=v,zone=f'{zone:05o}',
                    aligned_nonzero=aligned,nonzero_union=union,
                    shared_distinctive=shared,whole_page_candidate=whole)
                candidates.append(row)
                if whole:
                    key=(v,zone)
                    if key not in selected or aligned>selected[key]['aligned_nonzero']:
                        selected[key]=row
    groups={}
    for (v,zone),row in selected.items():
        image=raw[v][zone*6144:(zone+1)*6144]
        key=(row['family'],digest(image))
        groups.setdefault(key,[]).append((v,zone))
    variants=[]
    parse=runpy.run_path(str(ROOT/'tests/echolot-layout.py'))['parse_instructions']
    for (family,sha),locations in sorted(groups.items()):
        locations.sort();v,zone=locations[0]
        reference_zone,load,symbols=REFERENCES[family]
        image=raw[v][zone*6144:(zone+1)*6144]
        name=f'{family}-{v}-{zone:05o}'
        binary=out/(name+'.bin');binary.write_bytes(image)
        if family=='СБОЙ' and zone==0o64:symbols='СБОЙ-0064.sym'
        command=[str(args.disassembler),'-b',f'-a{load:o}',f'-e{load:o}',
                 '-n',str(ROOT/'syms'/symbols),str(binary)]
        result=subprocess.run(command,capture_output=True,text=True,check=True)
        assert not result.stderr.strip(),result.stderr
        (out/(name+'.stderr')).unlink(missing_ok=True)
        listing=result.stdout.replace('Code: 6144 (02000) words','Code: 1024 (02000) words; 6144 bytes')
        ref=pages['2248'][reference_zone];words=pages[v][zone]
        differences=[dict(address=f'{load+i:05o}',offset=f'{i:04o}',
            original=f'{a:012X}',variant=f'{b:012X}')
            for i,(a,b) in enumerate(zip(ref,words)) if a!=b]
        locations_text=', '.join(f'{vv}:{zz:05o}' for vv,zz in locations)
        header=f'* {family}: {locations_text}; load {load:05o}; SHA256 {sha}\n'
        header+='* Static disassembly; independent entry seeds.\n' if symbols in ('СБОЙ-0064.sym','КСБRUN.sym') else '* Catalog symbol map; static disassembly.\n'
        if load==0:header+=f'* Word 00000 (suppressed by disbesm6): {words[0]:016o}\n'
        (out/(name+'.lst')).write_text(header+listing)
        dump=subprocess.run(['besmtool','dump',v,f'--start=0{zone:o}','--length=1'],
            capture_output=True,text=True,check=True,cwd='/usr/local/share/besm6')
        (out/(name+'.dump')).write_text(dump.stdout)
        # Only compare code/data classifications for images sharing the layout.
        code=None
        if symbols not in ('СБОЙ-0064.sym','КСБRUN.sym'):
            kinds={}
            for line in (ROOT/'syms'/symbols).read_text().splitlines():
                f=line.split()
                if not f or f[0].startswith('#') or f[1]=='520':continue
                bounds=[int(a,8) for a in f[0].split('-')]
                for a in range(bounds[0],bounds[-1]+1):kinds[a]=f[1] in ('C','B','A')
            code=sum(kinds.get(int(d['address'],8),False) for d in differences)
        variant=dict(name=name,family=family,load=f'{load:05o}',sha256=sha,
            locations=[dict(volume=vv,zone=f'{zz:05o}') for vv,zz in locations],
            symbols=symbols,words=1024,nonzero_words=sum(bool(w) for w in words),
            reference=f'2248:{reference_zone:05o}',different_words=len(differences),
            different_code_words=code,differences=differences,
            decoded_halfwords=len(parse(result.stdout)),
            binary=binary.name,listing=name+'.lst',dump=name+'.dump')
        variants.append(variant)
        (out/(name+'.diff.json')).write_text(json.dumps(variant,ensure_ascii=False,indent=2)+'\n')
        print(f"{locations_text}: {family}, {len(differences)} differences, {variant['decoded_halfwords']} decoded halves")
    for v,p in disks.items():assert digest(p.read_bytes())==hashes[v],v
    report=dict(source_disks_sha256=hashes,source_disks_unchanged=True,
        zone_counts={v:len(p) for v,p in pages.items()},
        criteria=dict(minimum_distinctive=20,whole_page_aligned_nonzero=500,
                      whole_page_distinctive=200),variants=variants,candidates=candidates)
    (out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    index=['# ПУЛЬТ: варианты резидентных страниц','',
        'Зоны и адреса восьмеричные. Каждая строка — один SHA-256 образа.',
        'Сравнение — с указанной опорной зоной 2248; нули исключены из поискового рейтинга.','',
        '| Семейство | Расположение | Опорная зона | Различий слов | Файлы |',
        '|---|---|---|---:|---|']
    for v in variants:
        locations=', '.join(x['volume']+':'+x['zone'] for x in v['locations'])
        links=' / '.join(f'[{label}]({v[key]})' for label,key in
                         (('листинг','listing'),('полный dump','dump'),('образ','binary')))
        index.append(f"| {v['family']} | {locations} | {v['reference']} | {v['different_words']} | {links} |")
    index+=['','[Полный отчёт поиска и сравнения](report.json).',
        'Для СБОЙ-0064 и КСБRUN заданы собственные входы без переноса разметки другого резидента.',
        'В полном dump декодированы обе половины всех слов; листинг отделяет данные от достижимого кода.']
    (out/'README.md').write_text('\n'.join(index)+'\n')
    print(f'{len(variants)} distinct images, {len(selected)} zone occurrences; source disks unchanged')


if __name__=='__main__':main()
