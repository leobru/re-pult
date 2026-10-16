#!/usr/bin/env python3
# Print the ПУЛЬТ catalog (zone 01000 of the system volume).
#
# Word 0 is the catalog header; then pairs: a 6-character GOST name and a word
# with the start zone (left half) and the length in zones (right half). Zones
# are relative to the catalog volume offset (unit 40 = <vol>-1000), so the
# absolute zone is 01000 + start. The list ends with a zero name.
#
# usage: tools/catalog.py [VOL [ZONE]]     default 2248 01000
import os, subprocess, sys, tempfile
sys.path.insert(0, os.path.dirname(__file__))
from gost import text

vol = sys.argv[1] if len(sys.argv) > 1 else '2248'
zone = int(sys.argv[2], 8) if len(sys.argv) > 2 else 0o1000
with tempfile.TemporaryDirectory() as d:
    f = os.path.join(d, 'z.bin')
    subprocess.run(['besmtool', 'dump', vol, '--start=0%o' % zone, '--length=1',
                    '--to-file=' + f], check=True, stdout=subprocess.DEVNULL)
    b = open(f, 'rb').read()
w = lambda i: b[i * 6:i * 6 + 6]
print('header: %s  (%s)' % (text(w(0)), w(0).hex()))
i = 1
while i + 1 < 1024 and any(w(i)):
    d = int.from_bytes(w(i + 1), 'big')
    start, n = d >> 24, d & 0xffffff
    print('%04o  %-6s  zone %04o (abs %05o)  len %3o' %
          (i, text(w(i)), start, zone + start, n))
    i += 2
print('%04o  end; next word %016o' % (i, int.from_bytes(w(i + 1), 'big')))
