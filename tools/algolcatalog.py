#!/usr/bin/env python3
"""Read the BESM-ALGOL _БИБ catalog (physical drum 21, tracks 020–021).

Example: python3 tools/algolcatalog.py 2248 --compare 2148 --markdown
Addresses printed by this tool are octal. Only catalog data is decoded.
"""
import argparse
import hashlib
import sys
from pathlib import Path

from extract import dump
from gost import text


def source(data, offset):
    """Return bytes up to the first zero word, as read by 01202/01676."""
    start = offset * 6
    for end in range(start, len(data), 6):
        if data[end:end + 6] == bytes(6):
            return data[start:end]
    raise ValueError('no zero word terminating algorithm text')


def source_text(data):
    """Strip the odd-parity bit; zero padding bytes become line breaks."""
    return ''.join('\n' if c == 0 else text(bytes([c & 0x7f])) for c in data)


def gost_name(name):
    return name.upper().translate(str.maketrans('ABCEHKMOPTXY', 'АВСЕНКМОРТХУ'))


def catalog(data):
    if len(data) != 2 * 1024 * 6:
        raise ValueError('expected two catalog zones')
    words = [int.from_bytes(data[i:i + 6], 'big')
             for i in range(0, len(data), 6)]
    end = words[1] + 1
    if not 0o63 < end <= 0o2000:
        raise ValueError('catalog end outside the two pages')
    entries, seen = [], set()
    for bucket in range(5, 0o63):
        link = words[bucket]
        while link:
            if not 0o63 <= link < end or link in seen:
                raise ValueError(f'invalid or repeated link {link:o}')
            seen.add(link)
            descriptor = words[link]
            name, i = bytearray(), link + 1
            while i < end:
                word = words[i]
                name.extend(c & 0x7f for c in data[i * 6:(i + 1) * 6])
                i += 1
                if word & (1 << 47):
                    break
            else:
                raise ValueError(f'unterminated name at {link:o}')
            name = bytes(name).split(b'\x7e', 1)[0]
            if not name or name[0] - 0o33 != bucket:
                raise ValueError(f'name in wrong bucket at {link:o}')
            dependencies, dep = [], (descriptor >> 12) & 0xfff
            if dep:
                while dep < end:
                    parts = [(words[dep] >> shift) & 0xfff
                             for shift in (36, 24, 12, 0)]
                    dependencies.extend(p for p in parts[:next(
                        (j for j, p in enumerate(parts) if not p), 4)])
                    if 0 in parts:
                        break
                    dep += 1
                else:
                    raise ValueError('unterminated dependency list')
            entries.append(dict(name=text(name), record=link,
                                offset=(descriptor >> 24) & 0x7fffff,
                                descriptor=descriptor,
                                dependencies=dependencies))
            link = descriptor & 0xfff
    by_record = {e['record']: e for e in entries}
    for entry in entries:
        entry['dependencies'] = [by_record[p]['name']
                                 for p in entry['dependencies']]
        if not 0o2000 <= entry['offset'] < words[3]:
            raise ValueError('algorithm offset outside library')
    return words, entries


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('volume', nargs='?', default='2248')
    parser.add_argument('--zone', type=lambda s: int(s, 8), default=0o320)
    parser.add_argument('--compare', metavar='VOLUME')
    parser.add_argument('--markdown', action='store_true')
    parser.add_argument('--extract', metavar='NAME', help='extract one algorithm')
    parser.add_argument('--output', type=Path, help='decoded source output file')
    parser.add_argument('--raw-output', type=Path, help='original bytes with parity')
    args = parser.parse_args()
    data = dump(args.volume, args.zone, 2)
    words, entries = catalog(data)
    zones = (words[3] + 1023) // 1024
    library = dump(args.volume, args.zone, zones)
    print(f'Volume {args.volume}, zones {args.zone:04o}–'
          f'{args.zone + zones - 1:04o}: {len(entries)} names.')
    print(f'Last catalog word: {words[1]:04o}; library boundary: {words[3]:06o}.')
    print('SHA-256 (up to library boundary): '
          + hashlib.sha256(library[:words[3] * 6]).hexdigest())
    if args.compare:
        other = dump(args.compare, args.zone, zones)
        if library != other:
            raise ValueError(f'library zones differ from {args.compare}')
        print(f'All {zones} complete zones match volume {args.compare}.')
    if args.extract:
        matches = [e for e in entries if e['name'] == gost_name(args.extract)]
        if len(matches) != 1:
            raise ValueError('algorithm not found: ' + args.extract)
        entry = matches[0]
        raw = source(library, entry['offset'])
        bad = sum(bool(c) and c.bit_count() % 2 == 0 for c in raw)
        print(f"{entry['name']}: {len(raw) // 6} words before zero word; "
              f'{bad} nonzero bytes fail odd parity.')
        if args.raw_output:
            args.raw_output.write_bytes(raw)
        if args.output:
            args.output.write_text(source_text(raw))
        else:
            print(source_text(raw))
        return
    print()
    if args.markdown:
        print('| Имя (ГОСТ) | Запись | Смещение | Зона.слово | Зависимости |')
        print('|---|---:|---:|---:|---|')
    for entry in entries:
        offset = entry['offset']
        location = f'{args.zone + offset // 1024:04o}.{offset % 1024:04o}'
        deps = ', '.join(entry['dependencies']) or '—'
        if args.markdown:
            print(f"| {entry['name']} | {entry['record']:04o} | "
                  f'{offset:06o} | {location} | {deps} |')
        else:
            print(f"{entry['name']:<20} {entry['record']:04o} "
                  f'{offset:06o} {location} {deps}')


if __name__ == '__main__':
    try:
        main()
    except (ValueError, KeyError) as error:
        sys.exit(str(error))
