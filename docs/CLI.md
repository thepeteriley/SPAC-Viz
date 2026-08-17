# Command-line guide

The installed entry point is `spac-viz`. Run `spac-viz --help` for the complete
option list and current defaults.

## Choose an input

Exactly one source is required:

```bash
spac-viz --adapt-file map.fts.gz ...
spac-viz --download-latest ...
spac-viz --download-time 2026-07-30T12:00:00 ...
```

`--realization` accepts an ensemble plane index or `mean`. Download-by-time
selects the closest result within three hours. Latest-download mode searches
the preceding 14 days by default; adjust it with `--download-recent-days`.

## PFSS and seed controls

| Option | Default | Meaning |
|---|---:|---|
| `--rss` | `2.5` | Source-surface radius in solar radii |
| `--nrho` | `60` | PFSS radial grid count |
| `--surface-spacing-deg` | `2` | Photospheric angular grid spacing |
| `--outer-spacing-deg` | `2` | Source-surface spacing when enabled |
| `--outer-seeds` | off | Add a source-surface seed grid |
| `--trace-chunk-size` | `1000` | Seeds per atomic checkpoint |
| `--tracer` | `performance` | Maintained sunkit-magex tracer |

`theta` is colatitude: 0° is solar north and 180° is south. `phi` is
Carrington longitude in `[0, 360)`. Defaults avoid both poles and the duplicate
360° seam.

## Visualization

- `--plot` opens the interactive PyVista window.
- `--save-screenshot PATH` saves a PNG during rendering.
- `--save-pyvista PATH` writes combined line geometry as VTP.
- `--show-source-surface` adds a neutral outer wireframe.
- `--field-lines-only` removes all surfaces.
- `--orientation-diagnostic` labels cardinal Carrington longitudes and poles.
- `--off-screen` requests headless rendering; support depends on the VTK host.

The ADAPT magnetic map is shown only at `r=1 R_sun`; SPAC-Viz never displays or
implies an outer-radius magnetic map.

## Output and restart safety

Tracing checkpoints are atomically stored in `OUTPUT/checkpoints`. Interrupting
the process preserves completed chunks. Resume with the same arguments plus
`--resume`. SPAC-Viz validates a SHA-256 digest over model and tracing settings
before loading checkpoints.

Existing final products are refused unless `--overwrite` is provided. Use a
new directory whenever scientific configuration changes.

## VLA export

`--export-vla` creates the three required class files. `--vla-minimal` omits
the D4 header and metadata comments. `--vla-scale` scales coordinates during
export. `--export-combined-vla` creates an additional diagnostic file; it does
not replace the required class-specific files.
