# Scientific notes

## Model

SPAC-Viz computes a potential-field source-surface solution with
`sunkit_magex.pfss`. PFSS assumes a current-free magnetic field between a
spherical photosphere and a spherical source surface where the field becomes
radial. It is a useful global coronal approximation, not a time-dependent MHD
model.

## ADAPT handling

ADAPT FITS products normally contain 12 ensemble planes. SPAC-Viz explicitly
selects one plane or computes the pixelwise mean before constructing a SunPy
map. It validates that the WCS describes Carrington longitude/latitude magnetic
data. Native uniform-latitude CAR maps are converted using the maintained
WCS-aware `pfss.utils.car_to_cea()` helper immediately before PFSS construction.
No manual transpose, axis reversal, or longitude roll is applied.

## Coordinates

With colatitude `theta`, Carrington longitude `phi`, and radius `r`, internal
right-handed coordinates are:

```text
x = r sin(theta) cos(phi)
y = r sin(theta) sin(phi)
z = r cos(theta)
```

Digistar VLA output applies the required handedness-changing permutation and
writes `(X, Z, Y)` with `set coordsys LEFT`.

## Classification

A closed line reaches the photosphere at both endpoints. An open line reaches
the photosphere at one endpoint and the source surface at the other. Its sign
is bilinearly sampled from the original selected ADAPT map at the actual
photospheric endpoint, including periodic interpolation across the longitude
seam. Open lines are oriented from photosphere to source surface.

## Reproducibility

Record the ADAPT filename and observation time, ensemble realization, `rss`,
`nrho`, seed bounds and spacing, tracer and its parameters, endpoint tolerance,
classification threshold, simplification settings, and SPAC-Viz version.
`summary.json` and checkpoint manifests capture the core run configuration.

## Limitations

PFSS cannot represent coronal currents, eruptions, time evolution, or
non-spherical source surfaces. Classification and density depend on seed
placement and numerical tolerances. ADAPT realizations express different
plausible photospheric states and should not be treated as interchangeable.
