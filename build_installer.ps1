param(
    [switch]$RebuildApp
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$AppExe = Join-Path $ProjectRoot "dist\SpurGearCalculator\SpurGearCalculator.exe"
$IssFile = Join-Path $ProjectRoot "installer\SpurGearCalculator.iss"
$ReleaseDir = Join-Path $ProjectRoot "release"

Set-Location $ProjectRoot

function Resolve-IsccPath {
    $cmd = Get-Command ISCC.exe -ErrorAction SilentlyContinue
    if ($cmd) {
        return $cmd.Source
    }

    $candidates = @(
        "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        "C:\Program Files\Inno Setup 6\ISCC.exe"
    )

    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) {
            return $candidate
        }
    }

    return $null
}

if ($RebuildApp -or -not (Test-Path $AppExe)) {
    Write-Host "Building desktop app bundle with PyInstaller..." -ForegroundColor Cyan
    powershell -ExecutionPolicy Bypass -File ".\build.ps1"
    if ($LASTEXITCODE -ne 0) {
        throw "App build failed. Fix build issues first, then rerun build_installer.ps1."
    }
}

if (-not (Test-Path $AppExe)) {
    throw "Missing app executable: $AppExe"
}

if (-not (Test-Path $IssFile)) {
    throw "Missing installer script: $IssFile"
}

$iscc = Resolve-IsccPath
if (-not $iscc) {
    throw (
        "Inno Setup compiler was not found. Install Inno Setup 6 first, then rerun this script." +
        "`nDownload: https://jrsoftware.org/isdl.php"
    )
}

New-Item -ItemType Directory -Force $ReleaseDir | Out-Null

Write-Host "Using ISCC:" -ForegroundColor Cyan
Write-Host "  $iscc"
Write-Host "Compiling installer..." -ForegroundColor Cyan

& $iscc $IssFile
if ($LASTEXITCODE -ne 0) {
    throw "Installer compilation failed."
}

Write-Host ""
Write-Host "Installer build complete." -ForegroundColor Green
Write-Host "Output folder:" -ForegroundColor Green
Write-Host "  $ReleaseDir"
