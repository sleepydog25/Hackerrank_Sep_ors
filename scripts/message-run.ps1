param(
    [ValidateSet('extract','results')][string]$Mode = 'extract',
    [Parameter(ValueFromRemainingArguments=$true)][string[]]$RunArguments
)
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$configPath = Join-Path $repoRoot 'cache/message-config.json'
$settings = Get-Content -LiteralPath $configPath -Raw | ConvertFrom-Json
$env:MESSAGE_PROVIDER = $settings.provider
$env:MESSAGE_MODEL = $settings.model
$env:MESSAGE_INPUT_USD_PER_MILLION = $settings.input_per_million
$env:MESSAGE_OUTPUT_USD_PER_MILLION = $settings.output_per_million
$env:MESSAGE_CACHED_INPUT_USD_PER_MILLION = $settings.cached_input_per_million
$secretPointer = [IntPtr]::Zero
try {
    if ($Mode -eq 'extract') {
        $protectedKey = Get-Content -LiteralPath (Join-Path $repoRoot 'cache/openrouter-key.dpapi') -Raw
        $secureKey = ConvertTo-SecureString $protectedKey.Trim()
        $secretPointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureKey)
        $env:OPENROUTER_API_KEY = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($secretPointer)
    }
    $entry = if ($Mode -eq 'extract') { 'code/evaluation/message_extract.py' } else { 'code/evaluation/message_results.py' }
    & (Join-Path $repoRoot '.venv/Scripts/python.exe') (Join-Path $repoRoot $entry) @RunArguments
    $runExitCode = $LASTEXITCODE
} finally {
    Remove-Item Env:OPENROUTER_API_KEY -ErrorAction SilentlyContinue
    if ($secretPointer -ne [IntPtr]::Zero) { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($secretPointer) }
}
exit $runExitCode
