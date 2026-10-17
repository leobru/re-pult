#!/usr/bin/env python3
"""Verify volume provenance and run PULT/Pascal against private disk copies."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
ZONE = 8256
MASK = (1 << 48) - 1


def words(image, zone):
    offset = (zone + 4) * ZONE + 64
    return struct.unpack_from('<1024Q', image, offset)


def verify(directory):
    images = {v: (directory / v).read_bytes() for v in ('2148', '2248', '2068')}
    hashes = {v: hashlib.sha256(b).hexdigest() for v, b in images.items()}
    report = json.loads((directory / '2068.json').read_text())
    assert report['sha256'] == hashes['2068']
    assert len(report['zones']) == 0o120
    # Keep ПАСК's system-unit descriptor intact; only the unit's offset changes.
    assert words(images['2068'], 0o50)[0o1142] & MASK == 0o570007
    for entry in report['zones']:
        dest = int(entry['destination'], 8)
        src = int(entry['source'], 8)
        expected_volume = '2148' if (0o31 <= dest <= 0o33 or
                                     0o71 <= dest <= 0o72 or
                                     0o101 <= dest <= 0o114) else '2248'
        assert entry['volume'] == expected_volume
        assert src == dest + 0o1000
        source = words(images[expected_volume], src)
        actual = words(images['2068'], dest)
        patches = {int(p['word'], 8): int(p['new'], 16) for p in entry['patches']}
        for i, (old, new) in enumerate(zip(source, actual)):
            assert old >> 48 == new >> 48, (dest, i, 'tag')
            assert new & MASK == patches.get(i, old & MASK), (dest, i, 'payload')
        cw = struct.unpack_from('<8Q', images['2068'], (dest + 4) * ZONE)
        assert (cw[1] >> 12) & 0xfff == 2068
        assert (cw[0] >> 36) & 0xfff == 2 * (dest + 4)
        total = sum(w & MASK for w in actual)
        while total >> 48:
            total = (total & MASK) + (total >> 48)
        assert cw[3] & MASK == total
    # ГОРОСК replaces РЕЗРВ2 without moving or resizing the entry.
    catalog = words(images['2068'], 0)
    assert catalog[0o65] & MASK == 0x232e302e312a  # GOST ГОРОСК
    assert catalog[0o66] & MASK == (0o71 << 24) | 2
    assert catalog[0o16] & MASK == (0o7 << 24) | 0o17
    assert catalog[0o75] & MASK == 0x223f0f0f0f0f  # GOST BD
    assert catalog[0o76] & MASK == (0o26 << 24) | 1
    assert catalog[0o77] & MASK == 0
    assert catalog[0o377] & MASK == 0o77
    names = [catalog[i] & MASK for i in range(1, 0o77, 2)]
    assert 0x21202d242832 not in names  # БАНДИТ is internal, not callable.
    for dest in range(0o26, 0o31):
        assert words(images['2068'], dest) == words(images['2248'], dest + 0o1000)
    for dest in (0o71, 0o72):
        assert words(images['2068'], dest) == words(images['2148'], dest + 0o1000)
    # Catalog extents must remain relative to their own archive, not 01000.
    for catalog, extent in ((0, 0o100), (0o100, 0o20)):
        data = words(images['2068'], catalog)
        for i in range(1, 1023, 2):
            if not data[i] & MASK:
                break
            descriptor = data[i + 1] & MASK
            start, count = descriptor >> 24, descriptor & 0xffffff
            assert 0 < count and start + count <= extent

    spec = importlib.util.spec_from_file_location('make2068', ROOT / 'tools/make2068.py')
    generator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generator)
    manifest = json.loads((ROOT / 'tools/volume2068.json').read_text())
    rebuilt, _ = generator.build(directory / '2148', directory / '2248', manifest)
    assert rebuilt == images['2068']  # Includes deterministic control words.
    manifest['ranges'][0]['sha256'] = '0' * 64
    try:
        generator.build(directory / '2148', directory / '2248', manifest)
    except ValueError as error:
        assert 'source hash mismatch' in str(error)
    else:
        raise AssertionError('unchecked source accepted')
    manifest = json.loads((ROOT / 'tools/volume2068.json').read_text())
    manifest['patches'][0]['old'] = '000000000000'
    try:
        generator.build(directory / '2148', directory / '2248', manifest)
    except ValueError as error:
        assert 'patch mismatch' in str(error)
    else:
        raise AssertionError('unchecked patch accepted')
    return hashes


def main():
    app = Path(shutil.which(sys.argv[1]) or sys.argv[1]).resolve()
    directory = Path(sys.argv[2]).resolve()
    hashes = verify(directory)
    base = (ROOT / 'pult2068.b6').read_text()
    with tempfile.TemporaryDirectory(prefix='dispak-pult-') as temporary:
        temporary = Path(temporary)
        for volume in ('2148', '2248', '2068'):
            shutil.copyfile(directory / volume, temporary / volume)
            (temporary / volume).chmod(0o644)
        env = dict(os.environ, HOME=str(temporary))
        env.pop('BESM6_PATH', None)
        env.pop('BESM6_SMALL_DISKS', None)

        def session(name, commands, expected, deck=base, trace_words=(), forbidden_words=()):
            source = temporary / 'pult.b6'
            source.write_text(deck)
            result = subprocess.run(
                [str(app), '--725', '--path=' + str(temporary) + ':' + str(directory) + ':' +
                 str(app.parent) + ':/usr/local/share/besm6',
                 '-q', '-t', str(source)], input=commands, capture_output=True,
                text=True, env=env, cwd=temporary, timeout=25)
            for needle in expected:
                if needle not in result.stdout:
                    raise AssertionError(f'{name}: missing {needle!r}\n{result.stdout}\n{result.stderr[-3000:]}')
            assert result.returncode == 0, (name, result.stderr[-3000:])
            assert 'АВОСТ' not in result.stdout, (name, result.stdout)
            assert 'write-protected' not in result.stderr, name
            for word in trace_words:
                assert f'(={word})' in result.stderr, (name, word)
            for word in forbidden_words:
                assert f'(={word})' not in result.stderr, (name, word)
            print(name + ' passed')

        session('boot', 'конец\n', ['СИСТЕМА ПУЛЬТ', 'ВРЕМЯ РЕШ'],
                trace_words=('0010000000400040',))
        session('Pascal archive', 'арх PASCAL,40,100\nктл\nконец\n',
                ['ЕСТЬ', 'КВСЕ', 'КПЕЧ', 'КБИЛИС', 'КСБRUN'])
        session('BD dispatcher', 'арх сисбиб,40,0\nbd\nконец\n',
                ['ВD, А ДАЛЬШЕ'], trace_words=('0010000000400026',))
        # Latin BD selects the catalog's self-entry at 40:0030. Cyrillic
        # БД is a distinct name, pointing to the absent database at 40:0651.
        session('BD catalog', 'арх сисбиб,40,0\nbd open ктлBD\nbd ктл\n\n\nконец\n',
                ['КТЛБД', 'БД7154', 'БДО', 'БАЗА', 'ПИРИН', 'FFА', 'SIМ',
                 '0000Р0', 'НОВАЯ', 'БУФ1', 'БПИР', 'БДЛОТ', 'БДФОЙ',
                 'КТЛВD', 'ТУФТА', 'ЧИСЛА', 'БПАКП', 'ВОСЬМР'],
                trace_words=('0010360000400027', '0010340000400030'),
                forbidden_words=('0010340000400651',))
        session('service', 'сервис\nинф\nконец\n',
                ['ПАСКАЛЬ-СЕРВИС', 'ИСПОЛНЯЮТСЯ ПРИКАЗЫ', 'ДОЗАКАЗ'])
        for scratch in (False, True):
            deck = base if scratch else base.replace('лент 30(1С)^\n', '')
            operation = '3057003077000000' if scratch else '3757003077000000'
            session(f'БАВТ scratch={scratch}', 'бавт\nнет\nконец\n', ['ИДТИ?'], deck,
                    (operation, '0010000000301747', '0010370000301752'))
        session('ALG translator', 'алг\nконец\n', ['СТРОКА 2', 'В ЯЗЫКЕ НЕТ СИМВОЛА'],
                trace_words=('0010000000570015', '0014010000220034'))

        # Create a user archive through PULT, then supply a single source zone.
        archive = temporary / '2345'
        archive.write_bytes(bytes((0o200 + 4) * ZONE))
        deck = base.replace('лент 30(1С)^', 'лент 30(1С)^\nлент 50(2345-зп)^')
        session('user archive', 'дай новарх,50,100,вася\nарх вася,50,100,100\nз нов(30)\nконец\n',
                ['МСВ   НОВ    Н=001 Д=030'], deck)
        # Let ПУЛЬТ encode and save the source in СИС АЛГ mode. A space
        # terminates each reserved word; Щ sends OUTPUT to the terminal.
        session('ALG file compile and execute',
                (ROOT / 'tests/algol-shch.txt').read_text(),
                ['МСВ   АТЕСТ', '3.14159265358'], deck,
                trace_words=('0010000000570015', '0014010000220034'))
        # GOST fixture: _PROGRAM TEST; _BEGIN WRITELN(123); _END.
        letters = dict(zip('ABCDEFGHIJKLMNOPQRSTUVWXYZ',
                           (0o40, 0o42, 0o61, 0o77, 0o45, 0o100, 0o101, 0o55,
                            0o102, 0o103, 0o52, 0o104, 0o54, 0o105, 0o56, 0o60,
                            0o106, 0o107, 0o110, 0o62, 0o111, 0o112, 0o113, 0o65, 0o63, 0o114)))
        letters.update(zip('0123456789', range(10)))
        letters.update({'_': 0o132, ' ': 0o17, '\n': 0o175, '+': 0o12,
                        ':': 0o37, '=': 0o25, ';': 0o26, '(': 0o22, ')': 0o23, '.': 0o16})

        def source_text(program):
            text = (bytes(letters[c] for c in program) + bytes([0o172])).ljust(6144, b'\0')
            with archive.open('r+b') as stream:
                stream.seek((0o101 + 4) * ZONE + 64)
                stream.write(b''.join(struct.pack('<Q', int.from_bytes(text[i:i+6], 'big') | (2 << 48))
                                      for i in range(0, len(text), 6)))

        source_text('_PROGRAM TEST;\n_BEGIN WRITELN(123); _END.\n')
        session('Pascal compile and execute', 'арх вася,50,100\nпас нов\nконец\n',
                ['ПАСКАЛЬ-АВТОКОД 9.(09.12.88)', '       123 ', 'ВСЕ СДЕЛАНО.'], deck,
                ('0010000000400101', '0010000000570007', '0010040000570013'),
                ('0010000000400007',))
        source_text('_PROGRAM TEST;\n_VAR X: INTEGER;\n'
                    '_PROCED P; _BEGIN WRITELN(123) _END;\n'
                    '_FUNCTION F(X:INTEGER):INTEGER; _BEGIN F:=X+1 _END;\n'
                    '_BEGIN X:=F(122); P; WRITELN(X); _END.\n')
        expected = ['       123 \n       123 ', 'ВСЕ СДЕЛАНО.']
        session('Pascal variables/procedure/function', 'арх вася,50,100\nпас нов\nконец\n',
                expected + ['ПАСКАЛЬ-АВТОКОД 9.(09.12.88)'], deck)
        # Destroy the archive's unused assembler copy: compilation must still
        # use system-volume zones 0400–0404 through unit 57 at offset 0371.
        def erase_archive_assembler(image):
            image = bytearray(image)
            for zone in range(0o7, 0o14):
                start = (zone + 4) * ZONE + 64
                image[start:start + 8192] = bytes(8192)
            return image

        (temporary / '2068').write_bytes(erase_archive_assembler((directory / '2068').read_bytes()))
        for system in ('2148', '2248'):
            system_deck = deck.replace('57(2248-371)', f'57({system}-371)')
            session(f'Pascal with system {system}, archive assembler erased',
                    'арх вася,50,100\nпас нов\nконец\n',
                    expected + ['ПАСКАЛЬ-АВТОКОД 9.(09.12.88)'], system_deck,
                    ('0010000000570007', '0010040000570013'), ('0010000000400007',))
        # Run the identical program against the intact May compiler as oracle.
        spec = importlib.util.spec_from_file_location('make2068', ROOT / 'tools/make2068.py')
        generator = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(generator)
        manifest = json.loads((ROOT / 'tools/volume2068.json').read_text())
        manifest['ranges'] = [r for r in manifest['ranges'] if r['destination'] != '101']
        manifest['patches'] = [p for p in manifest['patches'] if p['zone'] != '114']
        may, _ = generator.build(directory / '2148', directory / '2248', manifest)
        (temporary / '2068').write_bytes(erase_archive_assembler(may))
        session('May compiler comparison', 'арх вася,50,100\nпас нов\nконец\n',
                expected + ['ПАСКАЛЬ-АВТОКОД 9.(17.05.88)'], deck)
    for volume, digest in hashes.items():
        assert hashlib.sha256((directory / volume).read_bytes()).hexdigest() == digest
    print('Provenance, tags, control words, catalogs, and source immutability passed')


if __name__ == '__main__':
    main()
