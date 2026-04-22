# Test Plan - Spur Gear Engineering Calculator v1.0

## 1. Objective
Verify release readiness for functionality, engineering accuracy, stability, usability, and export reliability.

## 2. Test Scope
- Input validation
- Solver accuracy
- UI behavior and responsiveness
- Gear preview rendering
- Export functionality
- Error handling

## 3. Environment
- OS: Windows desktop
- Python: `py -3`
- Dependencies from `requirements.txt`

## 4. Functional Test Matrix

### A. Input Validation
1. Enter non-numeric values in numeric fields.
2. Enter negative dimensions.
3. Enter `teeth` as non-integer or zero.
4. Leave all fields empty and click solve.
Expected:
- Inline errors and clear dialog/status guidance.
- No crash.

### B. Solvable Input Sets
Run solve with:
1. module + teeth
2. pitch diameter + teeth
3. outside diameter + teeth
4. pitch diameter + outside diameter
5. pitch diameter + root diameter
6. outside diameter + root diameter
Expected:
- Successful solve.
- Consistent result values.

### C. Conflict Detection
Enter conflicting dimensions and solve.
Expected:
- Input conflict message.
- No crash.

### D. Engineering Checks
After solve, open Engineering Checks tab.
Expected:
- Core equations listed.
- PASS/WARNING/ERROR style checks displayed.

### E. Preview Reliability
1. Solve and inspect preview visibility.
2. Use zoom in/out repeatedly.
3. Pan with mouse drag.
4. Click Fit and Reset.
5. Resize window and toggle panels.
Expected:
- Preview remains stable and recoverable.
- Annotation lines align with target labels.

### F. Workspace Controls
1. Hide/show inputs.
2. Hide/show results.
3. Expand/normal preview.
4. Full/Preview/Table mode buttons.
Expected:
- No overlap, no broken layout.

### G. Export Tests
1. Export CSV and open in Excel.
2. Export PDF and inspect values/units.
3. Export preview PNG and verify capture region.
4. Copy results and paste into text editor.
Expected:
- Complete data output.
- No export crashes.

## 5. Non-Functional Checks
- Repeated solve cycles (20+ runs).
- Rapid panel toggling.
- Repeated window resizing.
Expected:
- Smooth behavior and no instability.
