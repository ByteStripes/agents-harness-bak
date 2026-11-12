"""Execute two console programs with identical input files; does not debug them."""
import argparse
import hashlib
import json
import os
import subprocess
import time
from pathlib import Path


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('original', type=Path)
    parser.add_argument('candidate', type=Path)
    parser.add_argument('--input', action='append', required=True, type=Path, help='Raw stdin file; repeat for multiple cases')
    parser.add_argument('--out', required=True, type=Path, help='New results directory')
    parser.add_argument('--cwd', type=Path, help='Shared working directory; default is each executable parent')
    parser.add_argument('--arg', action='append', default=[], help='Shared program argument')
    parser.add_argument('--timeout', type=float, default=15)
    parser.add_argument('--execute', action='store_true', help='Explicitly enable target execution')
    args = parser.parse_args()
    if not args.execute:
        parser.error('No execution performed; --execute is required')
    if args.timeout <= 0:
        parser.error('--timeout must be positive')
    paths = [args.original.resolve(strict=True), args.candidate.resolve(strict=True)]
    inputs = [p.resolve(strict=True) for p in args.input]
    if args.cwd:
        args.cwd = args.cwd.resolve(strict=True)
    args.out.mkdir(parents=True, exist_ok=False)
    results = []
    for index, input_path in enumerate(inputs):
        row = {'input': str(input_path), 'input_sha256': digest(input_path), 'runs': []}
        for label, path in zip(('original', 'candidate'), paths):
            stdout_path = args.out / f'{index:03d}-{label}.stdout.bin'
            stderr_path = args.out / f'{index:03d}-{label}.stderr.bin'
            cwd = args.cwd or path.parent
            result = {'file': str(path), 'sha256': digest(path), 'cwd': str(cwd),
                      'arguments': args.arg, 'timed_out': False}
            start = time.monotonic()
            with input_path.open('rb') as stdin, stdout_path.open('wb') as stdout, stderr_path.open('wb') as stderr:
                try:
                    proc = subprocess.run([str(path), *args.arg], cwd=cwd, stdin=stdin,
                                          stdout=stdout, stderr=stderr, timeout=args.timeout,
                                          creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
                    result['exit_code'] = proc.returncode
                except subprocess.TimeoutExpired:
                    result['timed_out'] = True
                except OSError as error:
                    result['launch_error'] = str(error)
            result.update(elapsed_seconds=round(time.monotonic()-start, 3),
                          stdout=str(stdout_path.resolve()), stderr=str(stderr_path.resolve()),
                          stdout_sha256=digest(stdout_path), stderr_sha256=digest(stderr_path))
            row['runs'].append(result)
        first, second = row['runs']
        completed = all('exit_code' in r and not r['timed_out'] for r in row['runs'])
        row['completed_equivalent'] = completed and all(first[k] == second[k] for k in ('exit_code', 'stdout_sha256', 'stderr_sha256'))
        row['both_exit_zero'] = completed and all(r['exit_code'] == 0 for r in row['runs'])
        results.append(row)
        (args.out / 'comparison.json').write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding='utf-8')
    print(json.dumps({'cases': len(results), 'completed_equivalent': sum(r['completed_equivalent'] for r in results), 'report': str((args.out/'comparison.json').resolve())}))


if __name__ == '__main__':
    main()
