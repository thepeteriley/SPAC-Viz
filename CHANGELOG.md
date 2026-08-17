# Changelog

All notable changes to SPAC-Viz are documented here. This project follows
[Semantic Versioning](https://semver.org/).

## [1.0.0] - 2026-08-17

### Added

- Production ADAPT-to-PFSS tracing workflow using maintained sunkit-magex.
- Chunked, atomic, configuration-validated checkpoints and resume support.
- Closed, positive-open, negative-open, and unresolved classification.
- Deterministic field-line cleaning, orientation, and deduplication.
- Interactive PyVista visualization and VTP/screenshot export.
- Strict class-specific Digistar VLA export in the D4 coordinate convention.
- Official NSO fallback discovery for Carrington-centered ADAPT maps.

### Changed

- Renamed the project, package, and command to SPAC-Viz / `spac_viz` /
  `spac-viz`.
- Set the default photospheric and source-surface spacing to 2 degrees.
- Removed the unused explicit-intensity directive from VLA headers.

[1.0.0]: https://github.com/thepeteriley/SPAC-Viz/releases/tag/v1.0.0
