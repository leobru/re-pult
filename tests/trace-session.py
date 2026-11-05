#!/usr/bin/env python3
"""Check ALG coverage, timeout handling and isolation of the user's archive."""
import argparse
import hashlib
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dispak', default='dispak')
    args = parser.parse_args()
    out = ROOT / 'build/trace-session-tests'
    out.mkdir(parents=True, exist_ok=True)
    references = [ROOT / 'build/volumes/2250', Path.home() / '.besm6/2345']
    hashes = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in references if p.exists()}

    def run(name, session, timeout=5, app=args.dispak):
        target = out / name
        target.mkdir(exist_ok=True)
        # A failed rerun must invalidate a previous success marker.
        (target / '.done').touch()
        result = subprocess.run([sys.executable, str(ROOT / 'tools/trace-session.py'),
                                 str(session), str(target), '--volume', 'build/volumes/2250',
                                 '--catalog', 'images-2248.txt', '--dispak', app,
                                 '--timeout', str(timeout), '--', '--725'],
                                cwd=ROOT, capture_output=True, text=True, timeout=15)
        assert not (target / '.done').exists(), 'launcher retained a stale success marker'
        return result, target

    result, target = run('alg', ROOT / 'sessions/алг.txt')
    assert result.returncode == 0, result.stderr
    text = (target / 'terminal.txt').read_text(encoding='utf-8-sig')
    assert '123' in text and 'АВОСТ' not in text, text
    assert (target / 'АЛГ+0.trace').stat().st_size > 0
    assert (target / 'АЛГ+1.trace').stat().st_size > 0
    assert not list(target.glob('runtime-*')), 'private queue/disks survived the session'

    empty = out / 'empty-alg.txt'
    empty.write_text('алг\nконец\n')
    result, target = run('timeout', empty, timeout=0.25)
    assert result.returncode == 124 and 'timed out' in result.stderr, result.stderr
    assert (target / 'session.log').stat().st_size > 0

    result, _ = run('failed-emulator', ROOT / 'sessions/boot.txt', app='false')
    assert result.returncode == 1 and 'exit status 1' in result.stderr, result.stderr
    assert all(hashlib.sha256(p.read_bytes()).hexdigest() == old for p, old in hashes.items())
    print('Trace sessions: ALG printed 123; timeout and emulator errors propagated; reference disks unchanged')


if __name__ == '__main__':
    main()
