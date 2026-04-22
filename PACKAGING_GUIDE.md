# Packaging Guide - Spur Gear Engineering Calculator v1.0

## 1. Purpose
This guide defines the repeatable build and release process for desktop distribution.

## 2. Prerequisites
- Python 3 installed (`py -3`)
- Virtual environment active
- Dependencies installed:

```powershell
py -3 -m pip install -r requirements.txt
py -3 -m pip install -r requirements-build.txt
```

## 3. Pre-Build Checks
Run before packaging:

```powershell
py -3 -m py_compile gear_app.py gear_engine.py
py -3 gear_app.py
```

Manual verification checklist:
- Solve works for valid input combinations
- Preview zoom/fit/reset/pan works
- Exports (CSV/PDF/PNG/Copy) work
- Workspace toggles and modes work

## 4. Build Executable
If using provided script:

```powershell
.\build.ps1
```

If building directly with spec:

```powershell
py -3 -m PyInstaller spur_gear_calculator.spec --noconfirm
```

Expected output:
- `dist\SpurGearEngineeringCalculator\` (or spec-defined output)

## 4.1 Build Installer (Recommended for users)
Install Inno Setup 6:
- Download: https://jrsoftware.org/isdl.php

Then build installer:

```powershell
.\build_installer.ps1
```

If you want to force rebuild app bundle first:

```powershell
.\build_installer.ps1 -RebuildApp
```

Expected installer output:
- `release\SpurGearCalculatorSetup_v1.0.0_win64.exe`

Installer behavior:
- Installs app to Program Files
- Creates Start Menu shortcut
- Optional desktop shortcut
- Adds uninstall entry in Windows Apps settings

## 5. Release Artifact Naming
Recommended package name format:
- `SpurGearEngineeringCalculator_v1.0.0_win64.zip`

Include:
- Executable bundle from `dist`
- `README.md`
- `USER_GUIDE.md`
- `CHANGELOG.md`
- `LICENSE`

## 6. Integrity Checks
Generate hash for release artifact:

```powershell
Get-FileHash .\SpurGearEngineeringCalculator_v1.0.0_win64.zip -Algorithm SHA256
```

Store hash in release notes for verification.

## 7. Final Release Checklist
- Version in app UI matches release tag
- Changelog updated
- Test report completed
- Known issues documented
- Artifact launches on clean machine

## 8. Rollback Plan
If release issue is found:
1. Mark release as superseded/withdrawn.
2. Re-publish previous stable artifact.
3. Open patch branch and release `v1.0.1`.
