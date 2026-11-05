#!/usr/bin/env python3
"""Reassemble the recovered BD/BANDIT sources and compare full disk zones."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build/bandit-asm'
SOURCES = [('re-bd.asm', '01026'), ('re-bandit.asm', '01027')]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dispak', default=os.environ.get('DISPAK', 'dispak'))
    args = parser.parse_args()
    app = Path(shutil.which(args.dispak) or args.dispak).resolve()
    # Use the same historical assembler and RVS job as the ADSIS check.
    spec = importlib.util.spec_from_file_location('adsis_builder', ROOT / 'tools/build-adsis.py')
    assembler = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(assembler)
    disks = {v: Path('/usr/local/share/besm6') / v
             for v in ('2048', '2099', '2148', '2248')}
    hashes = {v: digest(p) for v, p in disks.items()}
    OUT.mkdir(parents=True, exist_ok=True)
    reports = []
    for filename, zone in SOURCES:
        folder = OUT / Path(filename).stem
        folder.mkdir(parents=True, exist_ok=True)
        home = folder / 'home'
        (home / '.besm6').mkdir(parents=True, exist_ok=True)
        env = dict(os.environ, HOME=str(home),
                   BESM6_PATH=str(folder) + ':/usr/local/share/besm6')
        env.pop('BESM6_SMALL_DISKS', None)

        def dump(volume, start, target):
            target.unlink(missing_ok=True)
            subprocess.run(['besmtool', 'dump', volume, '--start=' + start,
                            '--length=1', '--to-file=' + str(target)],
                           cwd=folder, env=env, check=True, stdout=subprocess.DEVNULL)
            data = target.read_bytes()
            assert len(data) == 6144, target
            return data

        originals = {v: dump(v, zone, folder / (v + '.bin')) for v in ('2148', '2248')}
        assert originals['2148'] == originals['2248'], zone
        source = ROOT / filename
        lines = source.read_text().expandtabs(8).splitlines()
        # BEMSH treats an empty card as an instruction with a missing opcode.
        cards = [line for line in lines if line.strip()]
        assert all(len(line) <= 72 or line.startswith('*') for line in cards), filename
        deck = folder / 'job.b6'
        deck.write_text(assembler.HEADER + ''.join(line + '^\n' for line in cards)
                        + assembler.TAIL.replace('074000', '000001'))
        (folder / '1234').write_bytes(b'')
        listing = folder / 'assembly.lst'
        with listing.open('w') as stream:
            result = subprocess.run([str(app), '--path=' + env['BESM6_PATH'], '-l', str(deck)],
                                    cwd=folder, env=env, stdin=subprocess.DEVNULL,
                                    stdout=stream, stderr=subprocess.STDOUT, timeout=60)
        text = listing.read_text(encoding='utf-8-sig').translate(
            str.maketrans('ABCEHKMOPTXY', 'АВСЕНКМОРТХУ'))
        errors = [int(n) for n in re.findall(r'ОШИБОК\s*=\s*(\d+)', text)]
        assert result.returncode == 0 and errors and not any(errors), listing
        assert 'МАКС СЕРЬЕЗН=0.' in text and 'АВОСТ' not in text, listing
        assert re.search(r'ЗОНГП\s*=\s*430001\s+СВ\.ЗОНА\s*=\s*430002', text), listing
        assert 'КОНЕЦ ЗАДАЧИ' in text, listing
        rebuilt = dump('1234', '1', folder / 'rebuilt.bin')
        old = originals['2148']
        differences = [dict(offset=f'{i // 6:04o}',
                            original=f'{int.from_bytes(old[i:i + 6], "big"):016o}',
                            rebuilt=f'{int.from_bytes(rebuilt[i:i + 6], "big"):016o}')
                       for i in range(0, 6144, 6) if old[i:i + 6] != rebuilt[i:i + 6]]
        report = dict(source=filename, source_sha256=digest(source),
                      original_zones=[v + ':' + zone for v in originals],
                      image_sha256=hashlib.sha256(old).hexdigest(),
                      rebuilt_sha256=hashlib.sha256(rebuilt).hexdigest(),
                      bytes=6144, identical_words=1024 - len(differences),
                      different_words=len(differences), differences=differences,
                      bemsh_errors=errors, omitted_blank_cards=len(lines) - len(cards),
                      load_address='000001')
        (folder / 'comparison.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
        reports.append(report)
    assert all(digest(p) == hashes[v] for v, p in disks.items()), 'Source disks changed'
    (OUT / 'report.json').write_text(json.dumps(dict(images=reports,
        source_disks_sha256=hashes, source_disks_unchanged=True), ensure_ascii=False, indent=2) + '\n')
    for report in reports:
        assert not report['differences'], report['source']
        print(report['source'] + ': BEMSH 0 errors; 1024/1024 words, 6144/6144 bytes; '
              + ', '.join(report['original_zones']))


if __name__ == '__main__':
    main()
