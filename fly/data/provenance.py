"""Helpers for writing dataset provenance manifests."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from fly.data.schemas import DatasetProvenance


def write_provenance_manifest(provenance: DatasetProvenance, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = asdict(provenance)
    destination.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
