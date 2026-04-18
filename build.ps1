param(
    [switch]$InstallBuildTool
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$DistDir = Join-Path $ProjectRoot "dist"
$BuildDir = Join-Path $ProjectRoot "build"
$SpecPath = Join-Path $ProjectRoot "spur_gear_calculator.spec"
$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

Set-Location $ProjectRoot

function Invoke-PythonCommand {
    param(
        [string[]]$Arguments,
        [string]$FailureMessage
    )

    & $script:PythonExe @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw $FailureMessage
    }
}

function Test-PythonRuntime {
    param(
        [string]$PythonExe,
        [string[]]$PrefixArgs
    )

    & $PythonExe @PrefixArgs "-c" "import encodings, tkinter; print('runtime-ok')"
    return $LASTEXITCODE -eq 0
}

$PythonExe = $null
$PythonArgsPrefix = @()

if ((Test-Path $VenvPython) -and (Test-PythonRuntime -PythonExe $VenvPython -PrefixArgs @())) {
    $PythonExe = $VenvPython
}
elseif (Test-PythonRuntime -PythonExe "py" -PrefixArgs @("-3")) {
    $PythonExe = "py"
    $PythonArgsPrefix = @("-3")
}
else {
    throw "No healthy Python runtime was found. Recreate .venv or repair your main Python installation first."
}

Write-Host "Using Python:" -ForegroundColor Cyan
Write-Host "  $PythonExe"

Invoke-PythonCommand -Arguments ($PythonArgsPrefix + @("--version")) -FailureMessage (
    "Python could not be started. If you have a local virtual environment, recreate it or install Python correctly."
)

if ($InstallBuildTool) {
    Write-Host "Installing PyInstaller..." -ForegroundColor Cyan
    Invoke-PythonCommand -Arguments ($PythonArgsPrefix + @("-m", "pip", "install", "-r", "requirements-build.txt")) `
        -FailureMessage "Failed to install build tools. Pip may be missing from this Python installation."
}

Write-Host "Checking for PyInstaller..." -ForegroundColor Cyan
Invoke-PythonCommand -Arguments ($PythonArgsPrefix + @("-m", "PyInstaller", "--version")) `
    -FailureMessage (
        "PyInstaller is not installed for the selected Python. Run .\build.ps1 -InstallBuildTool first."
    )

if (Test-Path $BuildDir) {
    Remove-Item -LiteralPath $BuildDir -Recurse -Force
}

if (Test-Path $DistDir) {
    Remove-Item -LiteralPath $DistDir -Recurse -Force
}

Write-Host "Building Spur Gear Calculator..." -ForegroundColor Cyan
Invoke-PythonCommand -Arguments ($PythonArgsPrefix + @("-m", "PyInstaller", "--clean", "--noconfirm", $SpecPath)) `
    -FailureMessage "PyInstaller failed while building the app."

Write-Host ""
Write-Host "Build complete." -ForegroundColor Green
Write-Host "Executable folder:" -ForegroundColor Green
Write-Host "  $DistDir\\SpurGearCalculator"
