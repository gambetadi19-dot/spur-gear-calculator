# Known Issues and Limitations (v1.0)

## 1. Scope Limitation
The calculator targets standard full-depth metric spur gears only.
- No helical/bevel/worm gear support.
- No profile shift or advanced standards modeling in v1.0.

## 2. PDF Export Format
PDF export is intentionally minimal for reliability.
- It produces a clean text report, not a styled engineering drawing sheet.

## 3. PNG Export Dependency
Preview PNG export requires Pillow (`ImageGrab`).
- If Pillow is missing, PNG export is unavailable.

## 4. Platform/UI Variability
Minor visual differences can occur by OS scaling and font rendering.
- Layout logic is responsive, but text wrapping may vary slightly.

## 5. Very Extreme Zoom/Pan
Very aggressive pan/zoom can temporarily move geometry out of view.
- Use `Fit` or `Reset` to recover instantly.

## 6. Planned Improvements (Post-v1.0)
- Automated unit/integration test suite.
- Optional styled PDF template.
- Extended engineering checks and standards packs.
