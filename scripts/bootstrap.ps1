param([string]$PythonExecutable)
$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
if (-not $PythonExecutable) {
    $bundled = Join-Path $env:USERPROFILE '.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
    if (Test-Path -LiteralPath $bundled) { $PythonExecutable = $bundled }
    else {
        $command = Get-Command python -ErrorAction SilentlyContinue
        if ($command) { $PythonExecutable = $command.Source }
        else { throw 'Pass -PythonExecutable with the full path to Python 3.12 or newer.' }
    }
}
& $PythonExecutable -c 'import sys; assert sys.version_info >= (3,12), "Python 3.12+ required"; print(sys.version)'
if ($LASTEXITCODE -ne 0) { throw 'Python version check failed' }
& $PythonExecutable -m venv --without-pip (Join-Path $repo '.venv')
if ($LASTEXITCODE -ne 0) { throw 'Virtual environment creation failed' }
Write-Output 'Ready: .\.venv\Scripts\python.exe (no activation or dependency downloads needed).'
