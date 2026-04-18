# Spur Gear Engineering Calculator

A desktop calculator for standard full-depth metric spur gears. The app can solve from multiple valid input combinations, reject conflicting geometry, and present the solved values in a cleaner engineering interface.

## Run The App

Open PowerShell in this folder and run:

```powershell
py -3 main.py
```

## Build A Downloadable Windows App

This project is prepared for packaging with PyInstaller.

### 1. Install the build tool

```powershell
py -3 -m pip install -r requirements-build.txt
```

Or use the included build script to install it for you:

```powershell
.\build.ps1 -InstallBuildTool
```

### 2. Build the app

```powershell
.\build.ps1
```

### 3. Find the packaged software

After a successful build, open:

`dist\SpurGearCalculator`

Inside that folder you should see `SpurGearCalculator.exe`. That folder is the downloadable app package you can zip and share with other Windows users.

## Recommended Share Format

For a simple first release:

1. Build the app.
2. Zip the full `dist\SpurGearCalculator` folder.
3. Rename the zip to something like `SpurGearCalculator-v1.0.0-win64.zip`.
4. Share that zip as your downloadable software.

## Notes

- The packaged app is set to `console=False`, so users will get a normal desktop window instead of a terminal.
- This packaging setup targets Windows because your project is a Tkinter desktop app and your current environment is Windows.
- If you want a more polished release later, the next step would be adding an app icon and a real installer such as Inno Setup.
