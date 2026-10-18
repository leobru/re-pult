#!/usr/bin/env python3
"""Probe БАВТ dispatch and launchers on isolated volume copies.

Absent unit 66 and the BEMSH return defect are expected failure cases.
"""
import argparse
import hashlib
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from gost import G

CASES = {
    'bemsh-star': 'бавт * 100',
    'bemsh-minus': 'бавт - 100',
    'form': 'форм 175 77 2 172 175\nформ',
    'form-bad': 'форм 400\nформ',
    'form-partial': 'форм 175 100000\nформ',
    'portion': 'порц 40',
    'portion-default': 'порц',
    'buffer': 'сбуф 1',
    'buffer-zero': 'сбуф 0',
    'buffer-limit': 'сбуф 40',
    'types': "мавт 1\nмавт 1.5\nмавт 'А'\nмавт =",
    'modes': 'па\nxyz\nппн\nxyz\nпп\nxyz',
    'zkan': 'зкан',
    'stat': 'статис',
    'time': 'врем',
    'stat-file': 'арх вася,50,100\nстатис первый',
    'concat': 'арх вася,50,100\nконкат первый метка второй',
    'concat-missing': 'арх вася,50,100\nконкат первый мимо второй',
    'unknown': 'арх вася,50,100\nнеизв',
    'raw': 'арх вася,50,100\nсырой',
    'raw-bad': 'арх вася,50,100\nплохой',
    'mavt-end': 'мавт',
    'editor': 'ред',
    'service': 'сервис\nинф',
    'demos': 'демос',
    'ent': 'энт',
    'bemsh': 'бавт\nнет',
    'bemsh-unpaged': 'порц 0\nбавт\nнет',
}

EXPECTED = {
    'bemsh-star': ('QU',),
    'bemsh-minus': ('QU',),
    'form': ('КОН СТР=175 ДЛИН=00077 ПРОГОН=2 КТ=172175',),
    'form-bad': ('НЕТ', 'КОН СТР=000'),
    'form-partial': ('НЕТ', 'КОН СТР=175 ДЛИН=00000'),
    'buffer-zero': ('НЕТ',),
    'buffer-limit': ('НЕТ',),
    'types': ('QU',),
    'zkan': ('НЕТ',),
    'stat': ('QU',),
    'time': ('ВЦП=',),
    'stat-file': ('ЧИСЛО СТРОК=1.СИМВОЛОВ=12.',),
    'concat': ('ЕСТЬ',),
    'concat-missing': ('!НЕТ ОБРАЗА',),
    'unknown': ('НЕИЗВ !',),
    'raw-bad': ('НЕ БУДУ ВЫПОЛНЯТЬ',),
    'mavt-end': ('НЕТ АВТОКОД ТРАНСЛЯТОРА',),
    'editor': ('ГДЕ ЖЕ ИМЯ ?',),
    'service': ('ПАСКАЛЬ-СЕРВИС',),
    'demos': ('АВОСТ 000042',),
    'ent': ('АВОСТ 000042',),
    'bemsh': ('ИДТИ?',),
    'bemsh-unpaged': ('АВОСТ 000030',),
}

EXPECTED_FAILURES = {'demos', 'ent', 'bemsh-unpaged'}


def gost(text):
    return int.from_bytes(bytes(G.index(c) for c in text.ljust(6)[:6]), 'big')


def write_zone(path, zone, words, tag=2):
    with path.open('r+b') as stream:
        stream.seek((zone + 4) * 8256 + 64)
        stream.write(b''.join(struct.pack('<Q', word | (tag << 48)) for word in words))


def make_archive(path):
    path.write_bytes(bytes((0o200 + 4) * 8256))
    catalog = [0] * 1024
    catalog[0] = gost('ВАСЯ')
    names = ('ПЕРВЫЙ', 'ВТОРОЙ', 'СЫРОЙ', 'ПЛОХОЙ')
    catalog[0o377] = 2 * len(names) + 1
    for i, name in enumerate(names):
        catalog[2 * i + 1] = gost(name)
        catalog[2 * i + 2] = ((i + 1) << 24) | 1
    write_zone(path, 0o100, catalog)
    write_zone(path, 0o101, [gost('АААААА'), gost('МЕТКА'), 0x7a7d00000000])
    write_zone(path, 0o102, [gost('ББББББ'), 0x7a7d00000000])
    # The assembly launch fixture has ::: in word 7 and instruction tags.
    write_zone(path, 0o103, [0] * 7 + [0o0307600216435072], tag=1)
    write_zone(path, 0o104, [0] * 8)


def check_case(name, terminal, trace):
    for fragment in EXPECTED.get(name, ()):
        assert fragment in terminal, (name, fragment, terminal[-1200:])
    if name not in EXPECTED_FAILURES:
        assert 'АВОСТ' not in terminal, (name, terminal[-1200:])
    if name == 'portion':
        assert '76421: store 0000000000000040' in trace
    if name == 'portion-default':
        assert '76421: store 0000000000000000' in trace
    if name == 'buffer':
        assert '(=0010040000270000)' in trace
    if name == 'types':
        assert terminal.count('QU') == 4
    if name == 'modes':
        assert terminal.count('СТОИТ') == 2
    if name == 'concat':
        copies = re.findall(r'^66654: \*75.*r\[6\]=([0-7]+)', trace, re.M)
        assert len(copies) == 1026 and copies[0] == '10001' and copies[-1] == '12002'
        assert re.search(r'^66654: xta .*\(=1022044110220441\)', trace, re.M)
    if name == 'concat-missing':
        assert not re.search(r'^66654: \*75', trace, re.M)
    if name == 'raw':
        assert re.search(r'^00007: uj  76002', trace, re.M)
    if name == 'raw-bad':
        assert not re.search(r'^00007:', trace, re.M)
    if name == 'stat':
        assert not re.search(r'^74036:', trace, re.M)
    if name == 'stat-file':
        assert re.search(r'^74036:', trace, re.M)
    if name == 'bemsh':
        assert '(=3057003077000000)' in trace
    if name == 'bemsh-unpaged':
        assert re.search(r'^67163: \*72 67304.*3040003077000000', trace, re.M)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dispak', default='dispak')
    parser.add_argument('--volumes', type=Path, default=ROOT / 'build/volumes')
    parser.add_argument('--output', type=Path, default=ROOT / 'build/bavt-check')
    parser.add_argument('--case', action='append', choices=sorted(CASES))
    args = parser.parse_args()
    app = str(Path(shutil.which(args.dispak) or args.dispak).resolve())
    volumes, output = args.volumes.resolve(), args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    hashes = {v: hashlib.sha256((volumes / v).read_bytes()).digest()
              for v in ('2248', '2068')}
    selected = {name: cmd for name, cmd in CASES.items()
                if not args.case or name in args.case}
    for name, commands in selected.items():
        with tempfile.TemporaryDirectory(prefix='pult-bavt-') as temporary:
            temporary = Path(temporary)
            for volume in hashes:
                shutil.copyfile(volumes / volume, temporary / volume)
            make_archive(temporary / '2345')
            deck = (ROOT / 'pult2068.b6').read_text().replace(
                'лент 30(1С)^', 'лент 30(1С)^\nлент 50(2345-зп)^')
            if name == 'mavt-end':
                deck = deck.replace('еконец', 'в 10000\nс 1466000000000000\nеконец')
            job = temporary / 'job.b6'
            job.write_text(deck)
            commands += '\nконец\n'
            (output / f'{name}.input').write_text(commands)
            env = dict(os.environ, HOME=str(temporary))
            for key in ('BESM6_PATH', 'BESM6_SMALL_DISKS'):
                env.pop(key, None)
            trace_flags = ['-t'] if name.startswith('bemsh') else ['-t', '-t']
            with (output / f'{name}.out').open('w') as stdout, \
                    (output / f'{name}.trace').open('w') as stderr:
                result = subprocess.run(
                    [app, '--725', '--path=' + str(temporary) + ':/usr/local/share/besm6',
                     '-q', *trace_flags, str(job)], input=commands, text=True,
                    stdout=stdout, stderr=stderr, env=env, cwd=temporary, timeout=15)
            terminal = (output / f'{name}.out').read_text()
            trace = (output / f'{name}.trace').read_text()
            assert result.returncode == 0, (name, result.returncode, terminal[-1200:])
            check_case(name, terminal, trace)
            suffix = ' (expected failure)' if name in EXPECTED_FAILURES else ''
            print(name + ': OK' + suffix, flush=True)
    assert all(hashlib.sha256((volumes / v).read_bytes()).digest() == digest
               for v, digest in hashes.items()), 'source volume changed'
    print(f'{len(selected)} cases checked; source volumes unchanged')


if __name__ == '__main__':
    main()
