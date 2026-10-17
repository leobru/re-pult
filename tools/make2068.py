#!/usr/bin/env python3
"""Build the relocated PULT/Pascal volume from checked physical-format images."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys
import tempfile

WORDS = 1024
ZONE = (WORDS + 8) * 8
MASK = (1 << 48) - 1


def payload(image, zone):
    start = (zone + 4) * ZONE + 64
    data = image[start:start + WORDS * 8]
    if len(data) != WORDS * 8:
        raise ValueError(f"missing source zone {zone:04o}")
    return data


def control_words(zone, data):
    # disk.c's default two-track format, with reproducible zero time/date/UID.
    checksum = sum(w & MASK for w in struct.unpack('<1024Q', data))
    while checksum >> 48:
        checksum = (checksum & MASK) + (checksum >> 48)
    first = ((zone + 4) * 2 << 36) | (0o30 << 21) | (1 << 3) | (2 << 48)
    second = (0o1370707 << 24) | (2068 << 12) | (2 << 48)
    return struct.pack('<8Q', first, second, 2 << 48, checksum | (2 << 48),
                       first + (1 << 36), second, 2 << 48, checksum | (2 << 48))


def build(source2148, source2248, manifest):
    sources = {'2148': Path(source2148).read_bytes(),
               '2248': Path(source2248).read_bytes()}
    selected = {}
    for entry in manifest['ranges']:
        start, dest, count = (int(entry[k], 8) for k in
                              ('start', 'destination', 'count'))
        chunks = [payload(sources[entry['volume']], start + i) for i in range(count)]
        if hashlib.sha256(b''.join(chunks)).hexdigest() != entry['sha256']:
            raise ValueError(f"source hash mismatch: {entry['volume']}:{start:04o}")
        for i, data in enumerate(chunks):
            selected[dest + i] = (entry['volume'], start + i, bytearray(data))
    provenance = []
    for dest, (vol, source, data) in sorted(selected.items()):
        before = bytes(data)
        changes = []
        for patch in manifest['patches']:
            if int(patch['zone'], 8) != dest:
                continue
            offset = int(patch['word'], 8) * 8
            word, = struct.unpack_from('<Q', data, offset)
            if word & MASK != int(patch['old'], 16):
                raise ValueError(f"patch mismatch: {dest:03o}:{patch['word']}")
            struct.pack_into('<Q', data, offset, (word & ~MASK) | int(patch['new'], 16))
            changes.append(patch)
        a, b = (struct.unpack('<1024Q', payload(sources[v], source))
                for v in ('2148', '2248'))
        provenance.append(dict(destination=f'{dest:03o}', volume=vol,
                               source=f'{source:04o}',
                               source_sha256=hashlib.sha256(before).hexdigest(),
                               sha256=hashlib.sha256(data).hexdigest(),
                               differing_words=sum(bool((x ^ y) & MASK) for x, y in zip(a, b)),
                               differing_tags=sum((x >> 48) != (y >> 48) for x, y in zip(a, b)),
                               patches=changes))
    # Full small-disk capacity; four reserved physical zones precede zone 0.
    image = bytearray((0o2000 + 4) * ZONE)
    for dest, (_, _, data) in selected.items():
        offset = (dest + 4) * ZONE
        image[offset:offset + ZONE] = control_words(dest, data) + data
    report = dict(volume=2068, source_sha256={v: hashlib.sha256(b).hexdigest()
                                             for v, b in sources.items()},
                  sha256=hashlib.sha256(image).hexdigest(), zones=provenance)
    return image, report


def atomic_write(path, data):
    path = Path(path)
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
        temporary = Path(stream.name)
        try:
            stream.write(data)
            stream.close()
            temporary.chmod(0o644)
            temporary.replace(path)
        finally:
            temporary.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--2148', dest='source2148', required=True)
    parser.add_argument('--2248', dest='source2248', required=True)
    parser.add_argument('--manifest', type=Path,
                        default=Path(__file__).with_name('volume2068.json'))
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.resolve() in {Path(args.source2148).resolve(), Path(args.source2248).resolve()}:
        parser.error('output must not overwrite a source image')
    try:
        image, report = build(args.source2148, args.source2248,
                              json.loads(args.manifest.read_text()))
        atomic_write(args.output.with_name(args.output.name + '.json'),
                     (json.dumps(report, indent=2) + '\n').encode())
        atomic_write(args.output, image)
    except (OSError, ValueError) as error:
        sys.exit(str(error))
    print(f"Created {args.output}: {len(report['zones'])} populated zones, SHA256 {report['sha256']}")


if __name__ == '__main__':
    main()
