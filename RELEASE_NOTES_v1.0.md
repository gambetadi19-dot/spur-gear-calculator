# Spur Gear Engineering Calculator v1.0 – Final Structure Documentation

## 1. Product Summary
**App Name:** Spur Gear Engineering Calculator  
**Version:** v1.0  
**Type:** Python desktop engineering tool (CustomTkinter + Tkinter canvas)  
**Purpose:** Solve standard full-depth metric spur gear geometry from valid input combinations, visualize geometry, run checks, and export results.

## 2. Project Structure
- [gear_app.py](/C:/Users/gambe/OneDrive/Desktop/PythonProject/gear_app.py)  
  UI layer, workspace controls, preview rendering, exports, user interactions.
- [gear_engine.py](/C:/Users/gambe/OneDrive/Desktop/PythonProject/gear_engine.py)  
  Engineering solver logic, validation, formulas, conflict detection.
- [main.py](/C:/Users/gambe/OneDrive/Desktop/PythonProject/main.py)  
  Entry wrapper (launches app).
- [requirements.txt](/C:/Users/gambe/OneDrive/Desktop/PythonProject/requirements.txt)  
  Runtime dependencies.
- [README.md](/C:/Users/gambe/OneDrive/Desktop/PythonProject/README.md)  
  Basic project notes.

## 3. Runtime Dependencies
Install in your venv:
```powershell
py -3 -m pip install -r requirements.txt
```

Key libraries:
- `customtkinter`
- `Pillow` (for PNG export via `ImageGrab`)

## 4. Architecture Overview
The app uses a clean 2-layer architecture:

1. **Engineering Layer** ([gear_engine.py](/C:/Users/gambe/OneDrive/Desktop/PythonProject/gear_engine.py))
- Input model: `GearInputs`
- Output model: `GearResult`
- Core solver: `auto_solve_gear(values)`
- Formula engine: `calculate_standard_spur_gear(...)`
- Consistency validation: `validate_against_entered_values(...)`
- Error model: `InputError`

2. **UI/Application Layer** ([gear_app.py](/C:/Users/gambe/OneDrive/Desktop/PythonProject/gear_app.py))
- Main class: `SpurGearCalculatorApp`
- Modern dashboard layout
- Field validation and status messaging
- Gear preview canvas + annotations + zoom/pan
- Export workflows (CSV/PDF/PNG/Copy)
- Workspace focus modes
- Help/About dialog

## 5. Engineering Model and Formulas
Implemented equations:
- `d = m × z` (pitch diameter)
- `da = m × (z + 2)` (outside diameter)
- `df = m × (z − 2.5)` (root diameter)
- `db = d × cos(phi)` (base diameter)
- `addendum = m`
- `dedendum = 1.25m`
- `circular_pitch = pi × m`
- `tooth_thickness = circular_pitch / 2`

Validation rules:
- Teeth must be integer `> 0`
- Pressure angle must be between `0` and `45` deg
- Dimensions must be positive
- Conflicting entered values raise `InputError` with clear message
- Minimum practical check: teeth `>= 3`

## 6. UI Structure (v1.0)
### Header
- Metallic gear logo
- App title
- Subtitle
- Visible release badge: `v1.0`
- Visible units line: `Units: Metric (mm), pressure angle in deg`

### Workspace Toolbar
- Hide/Show Inputs
- Hide/Show Results
- Expand/Normal Preview
- Modes:
  - Full View
  - Preview Focus
  - Table Focus
- Help / About button

### Left Panel (Inputs)
Grouped cards:
- Core Inputs
- Optional Diameter Inputs
- Derived Tooth Properties

Actions:
- Solve Gear
- Reset
- Load Example

### Right Panel (Results)
- Summary cards (Module, Teeth, Pitch Diameter, Base Diameter)
- Gear preview section
- Bottom tabs:
  - Geometry Table
  - Entered Values
  - Engineering Checks
  - Export

## 7. Preview System
Core capabilities:
- Dynamic preview drawing
- Accurate annotation mapping (outside/pitch/base/root)
- Leader lines terminate exactly on label Y-rows
- Zoom in/out
- Pan via drag
- Fit view (dynamic fit zoom)
- Reset view
- Error-safe fallback text if preview render fails

Important functions:
- `update_preview(...)`
- `compute_label_positions(...)`
- `map_geometry_to_lines(...)`
- `draw_annotations(...)`
- `_calculate_fit_zoom()`

## 8. Export System
Implemented exports:
- CSV
- PDF
- Preview PNG
- Copy Results to clipboard

Quality/stability:
- CSV uses `utf-8-sig` for Excel compatibility
- PDF includes title/version/units and full values list
- PNG captures preview canvas region
- All export paths have safe exception handling and user-friendly error dialogs

## 9. Error Handling Strategy
- Input errors: inline field errors + message box for conflicts
- Export errors: handled with `try/except` and clear dialog
- Preview render failures: contained and non-crashing
- Unexpected runtime errors: caught and surfaced cleanly

## 10. Versioning and Release Identity
In code:
- `APP_VERSION = "v1.0"`
- `UNITS_LABEL = "Units: Metric (mm), pressure angle in deg"`

Displayed in:
- Window title
- Header metadata
- Export outputs
- Clipboard output
- About dialog

## 11. Help/About Content
Dialog includes:
- App name
- Version
- Description
- Unit system
- Core formulas
- Assumptions/defaults (standard full-depth metric spur gear)

## 12. How to Run
From project folder:
```powershell
py -3 gear_app.py
```

Optional compile check:
```powershell
py -3 -m py_compile gear_app.py gear_engine.py
```

## 13. v1.0 Completion Statement
**Status:** v1.0 complete and release-ready.  
**Outcome:** Stable professional desktop engineering calculator with validated solver, polished UI, robust preview, and hardened exports.
