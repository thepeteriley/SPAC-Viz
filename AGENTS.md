# Codex Development Instructions

This repository contains a production Python application for converting ADAPT
photospheric magnetic maps into PFSS field-line visualizations and Digistar VLA
geometry.

## Start of Every Development Session

1. Read `README.md` and `HANDOFF.md`.
2. Inspect `git status` before modifying files.
3. Preserve user-generated FITS, NPZ, VTP, VLA, screenshot, and checkpoint
   outputs.
4. Activate the existing environment when available:

   ```bash
   source .venv/bin/activate
   ```

5. In restricted environments, use writable cache directories:

   ```bash
   export SUNPY_CONFIGDIR="$PWD/.sunpy-config"
   export SUNPY_DOWNLOADDIR="$PWD/.sunpy-data"
   export MPLCONFIGDIR="$PWD/.mpl-config"
   export XDG_CACHE_HOME="$PWD/.cache"
   ```

## Required Verification

After source changes, run:

```bash
SUNPY_CONFIGDIR=.sunpy-config \
SUNPY_DOWNLOADDIR=.sunpy-data \
MPLCONFIGDIR=.mpl-config \
XDG_CACHE_HOME=.cache \
PYVISTA_OFF_SCREEN=true \
.venv/bin/python -m pytest -q
```

Run `python -m compileall -q spac_viz spac_viz.py` after structural or
packaging changes.

Do not claim that a network download, full 1-degree trace, interactive render,
or screenshot was tested unless it was actually executed.

## Current Product Decisions

- Python 3.11 and 3.12 are supported.
- Use maintained `sunkit_magex.pfss`, never archived standalone `pfsspy`.
- The default angular spacing is 2 degrees.
- The default is photospheric-only seeding.
- Each maintained tracer already integrates every seed in both directions.
- Source-surface seeding is explicit with `--outer-seeds`.
- The ADAPT magnetic map at `r = 1 R_sun` is displayed by default.
- `--field-lines-only` removes every surface from the visualization.
- The source-surface wireframe appears only with `--show-source-surface`.
- Never display or imply an outer-radius magnetic map.
- VLA colors are filename/class labels; classic VLA does not encode RGB.
- Non-minimal VLA files must retain the approved D4 `set` header verbatim; it
  does not declare explicit intensity because no intensity records are emitted.
- VLA coordinates must be exported in input-axis order `X Z Y` with
  `set coordsys LEFT`; internal scientific coordinates remain `X Y Z`.
- Preserve the three required VLA filenames and their class assignments.
- Keep tracing chunked, checkpointed, resumable, and non-subsampled.
- Never bypass checkpoint compatibility validation.

## Data and Output Safety

Trace checkpoints are atomic and may be resumed with the same scientific
configuration, output directory, and `--resume`. A changed seed spacing,
realization, PFSS grid, tracer configuration, or outer-seed setting requires a
new output directory.

Do not delete or overwrite generated results unless the user explicitly
requests it. Avoid `git add .` because output directories can contain hundreds
of megabytes or more.

## Installed API Details

The verified environment used:

- Python 3.12.13
- SunPy 8.0.0
- sunkit-magex 1.1.0
- PyVista 0.47.3
- VTK 9.6.2

In sunkit-magex 1.1.0:

- `pfss.Input` uses the keyword `nr`, not `nrho`.
- `PerformanceTracer` accepts `step_size` and `max_steps`.
- `PythonTracer` exposes solver tolerances rather than those performance-tracer
  parameters.
- Native ADAPT CAR maps must be converted with the documented
  `pfss.utils.car_to_cea()` helper before PFSS construction.

Verify installed APIs again before changing compatibility code.
