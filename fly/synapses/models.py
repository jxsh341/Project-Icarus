from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Synapse:
    source: int
    target: int
    weight_or_count: float
    roi: Optional[str] = None
