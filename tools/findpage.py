#!/usr/bin/env python3
# Find zones on disk volumes that look like a given reference zone (e.g. a
# ПУЛЬТ page-37 image).
#
# For every zone of every volume it counts words equal to the reference at
# the same offset, and also reports zones that contain the reference's
# distinctive words at other offsets (a shifted or reassembled copy).
#
# usage: tools/findpage.py [--ref VOL:ZONE]... [--min N] VOL...
#   default reference: 2248:01035 (ПУЛЬТ page 37, 15.10.86) and 2248:01117
#   (page 37 of the monitor with the ЗАГР loader); default --min 20 distinctive words.
# Needs besmtool and the volume images in /usr/local/share/besm6.
import argparse, collections, os, subprocess, tempfile

def volume(vol):
    with tempfile.TemporaryDirectory() as d:
        f = os.path.join(d, 'v.bin')
        subprocess.run(['besmtool', 'dump', vol, '--to-file=' + f], check=True,
                       stdout=subprocess.DEVNULL, cwd='/usr/local/share/besm6')
        b = open(f, 'rb').read()
    w = [int.from_bytes(b[i:i+6], 'big') for i in range(0, len(b), 6)]
    return [w[i:i+1024] for i in range(0, len(w), 1024)]

ap = argparse.ArgumentParser()
ap.add_argument('--ref', action='append')
ap.add_argument('--min', type=int, default=20)
ap.add_argument('vols', nargs='+')
a = ap.parse_args()
refs = a.ref or ['2248:01035', '2248:01117']

vols = {}
def vz(v):
    if v not in vols:
        vols[v] = volume(v)
    return vols[v]

ref = {}
for r in refs:
    v, z = r.split(':')
    ref[r] = vz(v)[int(z, 8)]

# distinctive words: occur once in the reference, not 0 and not common
common = collections.Counter()
for v in a.vols:
    for zone in vz(v):
        common.update(set(zone))

for r, rw in ref.items():
    cnt = collections.Counter(rw)
    distinct = {w for w in rw if cnt[w] == 1 and w and common[w] <= 20}
    print('reference %s: %d distinctive words' % (r, len(distinct)))
    for v in a.vols:
        for z, zone in enumerate(vz(v)):
            same = sum(x == y for x, y in zip(zone, rw))
            shared = len(distinct & set(zone))
            if shared >= a.min:
                print('  %s zone %05o: %4d same place, %4d distinctive' %
                      (v, z, same, shared))
