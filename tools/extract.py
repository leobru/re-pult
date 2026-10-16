#!/usr/bin/env python3
# Extract every ПУЛЬТ catalog entry of a volume into images/<VOL>/<NAME>.bin
# (raw 6-byte words, as `besmtool dump --to-file` writes them), and each zone
# of a multi-zone entry as <NAME>+<k>.bin.
#
# usage: tools/extract.py VOL [ZONE]        default ZONE 01000
import os, subprocess, sys, tempfile
sys.path.insert(0, os.path.dirname(__file__))
from gost import text

def dump(vol, start, n):
    with tempfile.TemporaryDirectory() as d:
        f = os.path.join(d, 'z.bin')
        subprocess.run(['besmtool', 'dump', vol, '--start=0%o' % start,
                        '--length=%d' % n, '--to-file=' + f],
                       check=True, stdout=subprocess.DEVNULL)
        return open(f, 'rb').read()

def catalog(vol, zone=0o1000):
    """[(name, abs_zone, nzones)] of the catalog at `zone`."""
    b = dump(vol, zone, 1)
    w = lambda i: b[i * 6:i * 6 + 6]
    out, i = [], 1
    while i + 1 < 1024 and any(w(i)):
        d = int.from_bytes(w(i + 1), 'big')
        out.append((text(w(i)).rstrip(), zone + (d >> 24), d & 0xffffff))
        i += 2
    return out

if __name__ == '__main__':
    vol = sys.argv[1]
    zone = int(sys.argv[2], 8) if len(sys.argv) > 2 else 0o1000
    os.makedirs('images/' + vol, exist_ok=True)
    for name, z, n in catalog(vol, zone):
        b = dump(vol, z, n)
        open('images/%s/%s.bin' % (vol, name), 'wb').write(b)
        for k in range(n if n > 1 else 0):     # single zones, for overlay pools
            open('images/%s/%s+%o.bin' % (vol, name, k), 'wb').write(
                b[k * 6144:(k + 1) * 6144])
        print('%-7s %05o %3o' % (name, z, n))
