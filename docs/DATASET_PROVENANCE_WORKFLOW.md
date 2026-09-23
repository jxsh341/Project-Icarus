# Dataset Provenance Workflow

## Objective

Capture the exact MaleCNS dataset release, source metadata, raw artifacts, and checksums required for `FLY-BASE-001`.

## Workflow

1. Fetch the source and download pages into `data/raw/source_pages/`.
2. Record page fetch metadata with `scripts/fetch_url.py`.
3. Extract release/version/license/download links into `data/manifests/MaleCNS.provenance.json`.
4. Download raw biological artifacts into `data/raw/`.
5. Compute SHA-256 for each raw artifact and append to `data/checksums/raw_sha256.json`.
6. Update `data/manifests/dataset_inventory.csv` with the pinned dataset row.
7. Keep raw inputs immutable.

## Known current values

- source page: `https://janelia-flyem.github.io/male-cns/`
- download page: `https://janelia-flyem.github.io/male-cns/download/`
- neuPrint dataset: pending confirmation
- MaleCNS release/version: pending confirmation

## Notes

Web extraction via Firecrawl failed with HTTP 403 in this environment, so source-page acquisition should proceed via direct fetch/browser-based retrieval instead.
