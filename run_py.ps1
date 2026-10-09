param(
    [Parameter(ValueFromRemainingArguments=$true)]
    [string[]]$Command
)

$env:Path = [System.Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [System.Environment]::GetEnvironmentVariable('Path','User')
if (Test-Path "venv\Scripts\Activate.ps1") {
    . .\venv\Scripts\Activate.ps1
}
if ($Command) {
    Invoke-Expression "py $Command"
}
