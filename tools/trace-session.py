#!/usr/bin/env python3
"""Run one PULT coverage session with private disks and a bounded emulator."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    # Options after -- belong to dispak rather than this launcher.
    argv = sys.argv[1:]
    divider = argv.index('--') if '--' in argv else len(argv)
    flags = argv[divider + 1:]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('session', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--volume', type=Path, required=True)
    parser.add_argument('--catalog', type=Path, required=True)
    parser.add_argument('--dispak', default=os.environ.get('DISPAK', 'dispak'))
    parser.add_argument('--source-disks', type=Path, default=Path('/usr/local/share/besm6'))
    parser.add_argument('--timeout', type=float, default=30)
    args = parser.parse_args(argv[:divider])
    assert args.timeout > 0, 'timeout must be positive'
    app = shutil.which(args.dispak)
    if app is None:
        parser.error('dispak executable not found')
    session, output = args.session.resolve(), args.output.resolve()
    volume, catalog = args.volume.resolve(), args.catalog.resolve()
    output.mkdir(parents=True, exist_ok=True)
    (output / '.done').unlink(missing_ok=True)
    # Remove coverage from a previous execution of this session.
    for pattern in ('*.trace', '*.load'):
        for path in output.glob(pattern):
            path.unlink()
    log = output / 'session.log'
    terminal = output / 'terminal.txt'
    summary = output.with_suffix('.summary')
    search = [volume.parent]
    search += [Path(p).resolve() for p in os.environ.get('BESM6_PATH', '').split(':') if p]
    search += [Path.home() / '.besm6', args.source_disks.resolve()]
    with tempfile.TemporaryDirectory(prefix='runtime-', dir=output) as temporary:
        private = Path(temporary)
        # Unit 50 is writable in pult.b6. Never open the user's archive for writing.
        archive = next((folder / '2345' for folder in search if (folder / '2345').is_file()), None)
        if archive:
            shutil.copyfile(archive, private / '2345')
        else:
            (private / '2345').write_bytes(b'')
        env = dict(os.environ, DISPAK=str(Path(app).resolve()),
                   DISPAK_HOME=str(private / 'home'),
                   BESM6_PATH=os.pathsep.join(map(str, [private, *search])))
        status = 0
        with session.open('rb') as stdin, log.open('wb') as stream, terminal.open('wb') as stdout:
            try:
                result = subprocess.run([str(ROOT / 'tools/run-dispak.sh'), *flags,
                                         '-t', '-t', '-q', str(ROOT / 'pult.b6')],
                                        cwd=private, env=env, stdin=stdin,
                                        stdout=stdout, stderr=stream,
                                        timeout=args.timeout)
                status = result.returncode
            except subprocess.TimeoutExpired:
                status = 124
    # Retain useful coverage even on failure; Make must still see the failure.
    with log.open('rb') as trace, summary.open('wb') as stream:
        split = subprocess.run([sys.executable, str(ROOT / 'tools/phasetrace.py'),
                                str(output), str(catalog)], stdin=trace, stdout=stream)
    if status or split.returncode:
        reason = f'timed out after {args.timeout:g}s' if status == 124 else f'exit status {status or split.returncode}'
        print(f'{session.name}: {reason}; see {args.output / "session.log"}', file=sys.stderr)
        return status or split.returncode
    print(summary.read_text(), end='')
    return 0


if __name__ == '__main__':
    sys.exit(main())
