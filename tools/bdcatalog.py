#!/usr/bin/env python3
"""Print the single-block МАРС/БАНДИТ database catalog in PULT zone 030.

Field interpretation follows traced BD OPEN, not the PULT archive format.
Examples:
  python3 tools/bdcatalog.py 2248 --zone 01030
  python3 tools/bdcatalog.py --image build/volumes/2068 --zone 030
"""
import argparse
import json
from pathlib import Path
import struct

from extract import dump
from gost import text
from make2068 import MASK, payload

OFFSET = 0o1777
FIELD = 0o3776000


def decode(data):
    if len(data) != 6144:
        raise ValueError('expected one zone of 1024 six-byte words')
    words = [int.from_bytes(data[i:i + 6], 'big') for i in range(0, len(data), 6)]
    root = words[0]
    blocks = root >> 18
    if blocks != 1:
        raise ValueError(f'only single-block catalogs are supported, got {blocks:o}')
    if words[2] != 0:
        raise ValueError('not a first database block: word 002 is nonzero')
    directory = words[3] & OFFSET
    reserved = (words[3] & FIELD) >> 10
    count = words[-2]
    if not count or count % 2 or directory + count > 0o1776:
        raise ValueError('invalid directory bounds/count')
    if directory + reserved != 0o2000:
        raise ValueError('directory allocation does not extend to end of block')
    entries = []
    for address in range(directory, directory + count, 2):
        key, reference = words[address:address + 2]
        block, slot = reference & OFFSET, (reference & FIELD) >> 10
        if block != 0 or not 4 <= slot < directory or reference >> 20:
            raise ValueError(f'unsupported record reference at {address:04o}')
        descriptor = words[slot]
        offset, length = descriptor & OFFSET, (descriptor & FIELD) >> 10
        if descriptor >> 20 or length != 2 or offset + length > directory:
            raise ValueError(f'unsupported database record at slot {slot:03o}')
        metadata, location = words[offset:offset + length]
        entries.append(dict(name=text(key.to_bytes(6, 'big')).rstrip(),
                            key=f'{key:016o}', directory_word=f'{address:04o}',
                            reference=f'{reference:016o}', slot=f'{slot:03o}',
                            record_offset=f'{offset:04o}', record_words=f'{length:o}',
                            metadata=f'{metadata:016o}', location=f'{location:016o}',
                            unit=f'{(location >> 12) & 0o77:02o}',
                            zone=f'{location & 0o7777:04o}', blocks=f'{location >> 18:03o}'))
    return dict(root=f'{root:016o}', unit=f'{(root >> 12) & 0o77:02o}',
                zone=f'{root & 0o7777:04o}', blocks=f'{blocks:03o}',
                header_word1=f'{words[1]:016o}',
                directory_offset=f'{directory:04o}', directory_words=f'{count:03o}',
                directory_reserved_words=f'{reserved:03o}',
                footer_word1777=f'{words[-1]:016o}', entries=entries)


def markdown(result):
    lines = ['All numbers except the entry count are octal.', '',
             f"Entries: {len(result['entries'])}. Directory starts at "
             f"{result['directory_offset']}, length {result['directory_words']} words.", '',
             '| Name (GOST display) | Unit | First zone | Zones | Slot | Record words |',
             '|---|---|---|---|---|---|']
    for e in result['entries']:
        lines.append(f"| {e['name']} | {e['unit']} | {e['zone']} | {e['blocks']} | "
                     f"{e['slot']} | {e['record_offset']}–{int(e['record_offset'], 8) + 1:04o} |")
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('volume', nargs='?', default='2248')
    parser.add_argument('--image', type=Path, help='physical-format disk image path')
    parser.add_argument('--zone', type=lambda value: int(value, 8), help='octal source zone')
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()
    zone = args.zone if args.zone is not None else (0o30 if args.image else 0o1030)
    if args.image:
        physical = payload(args.image.read_bytes(), zone)
        data = b''.join((w & MASK).to_bytes(6, 'big') for w in struct.unpack('<1024Q', physical))
    else:
        data = dump(args.volume, zone, 1)
    try:
        result = decode(data)
    except ValueError as error:
        parser.error(str(error))
    print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else markdown(result))


if __name__ == '__main__':
    main()
