# Security policy

## Supported versions

Security fixes are applied to the latest release and the `main` branch.

## Reporting a vulnerability

Please use GitHub's private vulnerability reporting feature for this
repository rather than opening a public issue. Include the affected version,
reproduction steps, impact, and any suggested mitigation. Maintainers will
acknowledge a report as soon as practical and coordinate disclosure after a
fix is available.

SPAC-Viz processes local scientific data and can also retrieve files from
official NSO services. Treat untrusted FITS and checkpoint files as untrusted
input, and run large workflows with ordinary user privileges.
