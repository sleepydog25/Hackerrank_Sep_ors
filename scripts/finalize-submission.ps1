$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path $PSScriptRoot
$pythonExe = Join-Path $repoRoot '.venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $pythonExe)) { $pythonExe = 'python' }
& $pythonExe (Join-Path $repoRoot 'code/finalize_submission.py') --dataset (Join-Path $repoRoot 'dataset') --require-log
if ($LASTEXITCODE -ne 0) { throw 'Submission release failed; previous artifacts retained.' }
