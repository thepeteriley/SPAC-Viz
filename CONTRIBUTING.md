# Contributing to SPAC-Viz

Contributions that improve scientific correctness, reproducibility,
interoperability, documentation, and performance are welcome.

## Development setup

1. Fork and clone the repository.
2. Create a Python 3.11 or 3.12 virtual environment.
3. Install the package and test dependencies:

   ```bash
   python -m pip install -e '.[test]'
   ```

4. Create a focused branch from `main`.

## Tests

Run the full offline suite before opening a pull request:

```bash
SUNPY_CONFIGDIR=.sunpy-config \
SUNPY_DOWNLOADDIR=.sunpy-data \
MPLCONFIGDIR=.mpl-config \
XDG_CACHE_HOME=.cache \
PYVISTA_OFF_SCREEN=true \
python -m pytest -q
```

Run `python -m compileall -q spac_viz spac_viz.py` after package structure or
entry-point changes. Network tests are opt-in with `RUN_NETWORK_TESTS=1`.

## Scientific change requirements

- Add or update tests for coordinate, classification, tracing, or export logic.
- Preserve native ADAPT WCS semantics and use `pfss.utils.car_to_cea()`.
- Never introduce seed subsampling or bypass checkpoint compatibility checks.
- Keep internal scientific coordinates `(X, Y, Z)` distinct from VLA export
  order `(X, Z, Y)`.
- Report the exact configuration and data provenance for numerical comparisons.
- Do not commit FITS inputs or generated NPZ, VTP, VLA, screenshot, or
  checkpoint outputs.

## Pull requests

Keep changes narrowly scoped. Explain the motivation, verification performed,
scientific impact, and any compatibility implications. Do not claim a network
download, full 1° trace, or interactive render was tested unless it was run.
