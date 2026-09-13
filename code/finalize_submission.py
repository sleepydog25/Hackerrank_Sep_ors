"""Offline reproducible release. Validate staging before replacing known-good files."""
import argparse
import hashlib
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from buy_or_wait.load import load_dataset
from buy_or_wait.submission import write_output, validate_output

ROOT = Path(__file__).resolve().parents[1]
SECRET_PATTERNS = (
    rb'sk-(?:proj-)?[A-Za-z0-9_-]{20,}',
    rb'AIza[A-Za-z0-9_-]{30,}',
    rb'AQ\.[A-Za-z0-9_-]{25,}',
    rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',
    rb'(?i)(?:api[_-]?key|access[_-]?token|client[_-]?secret)\s*[=:]\s*[\x22\x27][A-Za-z0-9_-]{24,}[\x22\x27]',
)


def scan(name, content):
    if any(re.search(pattern, content) for pattern in SECRET_PATTERNS):
        raise ValueError(f'possible secret in {name}; content suppressed')


def usage_report(output):
    digest = hashlib.sha256(output).hexdigest()
    return f'''# Final submitted run usage

Strategy: deterministic S0, all 250 evaluation requests, frozen 90-day Python forecast
and Phase 3A reconciliation with no probabilistic evidence batches.

| Item | Final run |
|---|---:|
| Model provider / model | None / none |
| Model calls (external) | 0 |
| Cache hits / misses | 0 / 0 |
| Input tokens | 0 |
| Output tokens | 0 |
| Total tokens | 0 |
| Average tokens per request | 0 |
| Estimated total cost (USD) | 0 |
| Estimated cost per request (USD) | 0 |

Unvalidated probabilistic message and image extraction was disabled for the final run.
No historical extraction cache is read, relabeled, or replayed. Unknown cash amounts
or FX rates prevent plan certification; other unprocessed evidence remains explicitly
unresolved. Optional spending changes are disabled. Baseline capacity fields retain
the frozen structured-data calculation and can be provisional where evidence is missing.

This report covers only the application run producing the submitted output, not
development experiments or coding-assistant usage. Historical development usage,
including unknown attempts, remains separately documented and is not charged to this run.

Output SHA-256: `{digest}`

Reproduce: `python code/main.py --dataset dataset --output output.csv`
Release: `python code/finalize_submission.py --dataset dataset`
'''.encode('utf-8')


def inspect_archive(path, expected):
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)) or set(names) != set(expected):
            raise ValueError('archive manifest mismatch')
        if archive.testzip() is not None:
            raise ValueError('archive CRC failure')
        for name in names:
            parts = Path(name).parts
            if (name.startswith('/') or '..' in parts
                    or any(p in {'dataset','.venv','__pycache__','cache','.git'} for p in parts)
                    or Path(name).suffix in {'.sqlite','.dpapi'}
                    or Path(name).name in {'.env','log.txt'}):
                raise ValueError(f'forbidden archive member {name}')
            content = archive.read(name)
            if content != expected[name]:
                raise ValueError('archive content mismatch')
            scan(name, content)
        for required in ('code/main.py', 'code/finalize_submission.py', 'evaluation/usage_report.md', 'README.md'):
            if required not in names:
                raise ValueError(f'missing required member {required}')


def finalize(dataset_path, require_log=False):
    if require_log and not (ROOT/'log.txt').is_file():
        raise ValueError('root log.txt must remain separately available')
    data = load_dataset(dataset_path)
    # A failed build leaves both old root artifacts intact. Staged output and
    # archive are validated, scanned, and independently executed before promotion.
    with tempfile.TemporaryDirectory(prefix='submission-') as tmp:
        stage = Path(tmp)
        output = stage/'output.csv'
        rows = write_output(data, output)
        validate_output(data, output)
        output_bytes = output.read_bytes()
        report = usage_report(output_bytes)
        manifest = {p.relative_to(ROOT).as_posix(): p.read_bytes()
                    for p in sorted((ROOT/'code').rglob('*.py'))
                    if '__pycache__' not in p.parts}
        readme = ROOT/'SUBMISSION_README.md'
        if not readme.exists():
            readme = ROOT/'README.md'  # extracted submission
        manifest['README.md'] = readme.read_bytes()
        manifest['evaluation/usage_report.md'] = report
        for name in ('s0-release.md', 's0-sample-metrics.json'):
            path = ROOT/'evaluation'/name
            if path.is_file():
                manifest['evaluation/'+name] = path.read_bytes()
        launcher = ROOT/'scripts'/'finalize-submission.ps1'
        if launcher.is_file():
            manifest['scripts/finalize-submission.ps1'] = launcher.read_bytes()
        archive_path = stage/'code.zip'
        with zipfile.ZipFile(archive_path,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
            for name, content in sorted(manifest.items()):
                scan(name, content)
                info = zipfile.ZipInfo(name, date_time=(2026,1,1,0,0,0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                archive.writestr(info, content)
        inspect_archive(archive_path, manifest)
        unpacked = stage/'unpacked'
        with zipfile.ZipFile(archive_path) as archive:
            archive.extractall(unpacked)
        reproduced = stage/'reproduced.csv'
        subprocess.run([sys.executable, str(unpacked/'code'/'main.py'), '--dataset',
                        str(dataset_path.resolve()), '--output', str(reproduced)], check=True,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if reproduced.read_bytes() != output_bytes:
            raise ValueError('archive execution did not reproduce output')
        scan('output.csv', output_bytes)
        (ROOT/'evaluation').mkdir(exist_ok=True)
        # Same-directory atomic replacements, only after all release gates pass.
        for target, content in ((ROOT/'output.csv',output_bytes),
                                (ROOT/'evaluation'/'usage_report.md',report),
                                (ROOT/'code.zip',archive_path.read_bytes())):
            temporary = target.with_name(target.name+'.new')
            temporary.write_bytes(content)
            temporary.replace(target)
    print(f'Release passed: {len(rows)} rows; {len(manifest)} archive members; '
          'secret scan clean; archive execution byte-identical; model calls 0.')
    print(f'output.csv SHA-256: {hashlib.sha256(output_bytes).hexdigest()}')
    print(f'code.zip SHA-256: {hashlib.sha256((ROOT/"code.zip").read_bytes()).hexdigest()}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset',type=Path,default=ROOT/'dataset')
    parser.add_argument('--require-log',action='store_true')
    args = parser.parse_args()
    finalize(args.dataset,args.require_log)


if __name__ == '__main__':
    main()
