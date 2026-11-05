#!/usr/bin/env python3
"""Build a private 2068 with the checked BD MOD call-register correction."""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from make2068 import MASK, ZONE, control_words, payload, atomic_write

ROOT = Path(__file__).resolve().parents[1]


def patch_image(original, manifest):
    image = bytearray(original)
    for patch in manifest['patches']:
        zone, word = int(patch['zone'], 8), int(patch['word'], 8)
        data = bytearray(payload(image, zone))
        old, = struct.unpack_from('<Q', data, word * 8)
        assert old & MASK == int(patch['old'], 16), f'BD patch mismatch: {zone:o}:{word:04o}'
        struct.pack_into('<Q', data, word * 8, old & ~MASK | int(patch['new'], 16))
        start = (zone + 4) * ZONE
        image[start:start + ZONE] = control_words(zone, data) + data
    return image


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=ROOT / 'build/volumes/2068')
    parser.add_argument('--output', type=Path, default=ROOT / 'build/bd-private/2068')
    args = parser.parse_args()
    assert args.source.resolve() != args.output.resolve(), 'private volume must have its own path'
    original = args.source.read_bytes()
    manifest = json.loads((ROOT / 'patches-bd-private.json').read_text())
    image = patch_image(original, manifest)
    assembled = ROOT / 'build/bandit-asm-private/re-bd/rebuilt.bin'
    expected = b''.join((w & MASK).to_bytes(6, 'big')
                        for w in struct.unpack('<1024Q', payload(image, 0o26)))
    assert assembled.read_bytes() == expected, 'private source and checked disk patch disagree'
    engine = (ROOT / 'build/bandit-asm-private/re-bandit/rebuilt.bin').read_bytes()
    old_engine = payload(original, 0o27)
    words = []
    for i in range(1024):
        previous, = struct.unpack_from('<Q', old_engine, i * 8)
        value = int.from_bytes(engine[i*6:i*6+6], 'big')
        tag = 1 << 48 if 0o1162 <= i < 0o1763 and value else previous & ~MASK
        words.append(tag | value)
    data = struct.pack('<1024Q', *words)
    start = (0o27 + 4) * ZONE
    image[start:start + ZONE] = control_words(0o27, data) + data
    args.output.parent.mkdir(parents=True, exist_ok=True)
    atomic_write(args.output, image)
    assert args.source.read_bytes() == original
    report = dict(patches=manifest['patches'],
                  source_sha256=hashlib.sha256(original).hexdigest(),
                  private_sha256=hashlib.sha256(image).hexdigest(),
                  source_unchanged=True, assembled_zone_matches=True,
                  bandit_unchanged=payload(original, 0o27) == payload(image, 0o27))
    args.output.with_suffix('.json').write_text(json.dumps(report, indent=2) + '\n')
    print('Private BD/BANDIT: MOD reverse-copy routine installed; reference volume unchanged')


if __name__ == '__main__':
    main()
