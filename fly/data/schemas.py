"""Schema models for dataset provenance and manifests."""

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class RawArtifact:
    file_name: str
    source_url: str
    local_path: str
    size_bytes: int | None = None
    sha256: str | None = None
    downloaded_at: str | None = None
    notes: str | None = None


@dataclass(frozen=True)
class DatasetProvenance:
    dataset_name: str
    dataset_version: str | None
    release_date: str | None
    license_name: str | None
    license_url: str | None
    source_page: str
    download_page: str | None = None
    neuprint_dataset: str | None = None
    accessed_at: str | None = None
    artifacts: tuple[RawArtifact, ...] = ()
    extra: dict[str, Any] = field(default_factory=dict)
