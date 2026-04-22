# Spur Gear Engineering Calculator v1.0 - User Guide

## 1. Overview
Spur Gear Engineering Calculator is a desktop engineering tool for solving standard full-depth metric spur gear geometry from valid input combinations.

Units:
- Length: mm
- Pressure angle: deg

## 2. Installation
1. Open a terminal in the project folder.
2. Create and activate a virtual environment.
3. Install dependencies:

```powershell
py -3 -m pip install -r requirements.txt
```

## 3. Run the App
```powershell
py -3 gear_app.py
```

## 4. Input Rules
You only need a solvable combination. Common valid combinations:
- module + teeth
- pitch diameter + teeth
- outside diameter + teeth
- pitch diameter + outside diameter
- pitch diameter + root diameter
- outside diameter + root diameter

Validation rules:
- Teeth must be a positive whole number.
- Pressure angle must be between 0 and 45 deg.
- Numeric fields must be positive if entered.

## 5. Typical Workflow
1. Enter known values.
2. Click `Solve Gear`.
3. Review:
- Summary cards
- Gear preview
- Geometry table
- Engineering checks
4. Export or copy results.

## 6. Workspace Controls
- `Hide/Show Inputs`: collapse or restore left panel.
- `Hide/Show Results`: collapse or restore bottom tabs.
- `Expand/Normal Preview`: increase/decrease preview area.
- `Full View`: normal layout.
- `Preview Focus`: maximize preview workspace.
- `Table Focus`: emphasize tabular results.

## 7. Preview Controls
- `+` / `-`: zoom in/out
- `Fit`: auto fit gear to canvas
- `Reset`: reset zoom and pan
- Mouse wheel: zoom
- Drag: pan
- Double-click canvas: reset view

## 8. Export Features
- Export CSV: opens in Excel-compatible format.
- Export PDF: simple engineering report.
- Export Preview PNG: screenshot of preview panel.
- Copy Results: copies solved values to clipboard.

## 9. Help / About
Use `Help / About` in the toolbar for:
- version
- formula summary
- assumptions
- unit reference

## 10. Troubleshooting
- "Input conflict detected": entered values disagree; remove one conflicting value.
- "Not enough independent inputs": add one more independent known value.
- PNG export unavailable: install Pillow from requirements.
