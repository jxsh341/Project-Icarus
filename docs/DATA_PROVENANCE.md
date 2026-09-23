# Data Provenance

Track every raw biological artifact used in `FLY-BASE-001`.

## Required fields

- dataset name
- dataset version
- release date
- download source
- download date
- file name
- file size
- checksum
- license
- notes

## Policy

- Treat `data/raw/` as immutable.
- Do not mix releases without explicit documentation.
- Materialize live API-derived data into versioned local artifacts before using it in experiments.
