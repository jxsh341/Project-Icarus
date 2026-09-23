"""Tests for provenance manifest writing."""

import json
from pathlib import Path

from fly.data.provenance import write_provenance_manifest
from fly.data.schemas import DatasetProvenance, RawArtifact


def test_write_provenance_manifest_serializes_artifacts(tmp_path: Path) -> None:
    destination = tmp_path / "manifest.json"
    provenance = DatasetProvenance(
        dataset_name="MaleCNS",
        dataset_version="v0.9",
        release_date="2024-01-01",
        license_name="CC-BY-4.0",
        license_url="https://example.org/license",
        source_page="https://example.org/source",
        download_page="https://example.org/download",
        neuprint_dataset="male-cns:v0.9",
        accessed_at="2026-09-22",
        artifacts=(
            RawArtifact(
                file_name="neurons.csv",
                source_url="https://example.org/neurons.csv",
                local_path="data/raw/neurons.csv",
                size_bytes=123,
                sha256="abc",
            ),
        ),
    )

    write_provenance_manifest(provenance, destination)

    payload = json.loads(destination.read_text(encoding="utf-8"))
    assert payload["dataset_name"] == "MaleCNS"
    assert payload["neuprint_dataset"] == "male-cns:v0.9"
    assert payload["artifacts"][0]["file_name"] == "neurons.csv"
