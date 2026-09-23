from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class NeuronRecord:
    root_id: int
    cell_type: Optional[str] = None
    neurotransmitter: Optional[str] = None
    region: Optional[str] = None
    instance: Optional[str] = None
