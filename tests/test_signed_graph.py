"""Tests for neurotransmitter-sign edges in the canonical graph.

The Shiu et al. reference model weights every edge as
    w = sign(presynaptic NT) * synapse_count * w_syn
with sign strictly per presynaptic neuron (verified: zero mixed-sign
neurons among 138,005 in Connectivity_783.parquet; 32.5M excitatory vs
22.0M inhibitory synapses). Our canonical pipeline previously used raw
synapse counts for ALL edges - every GABAergic/glutamatergic edge acted
as excitation, which produced a runaway cascade at run-006 scale
(44% of the network spiking from a 2-neuron drive).

Convention (Eckstein et al. NT predictions; standard for adult Drosophila):
  acetylcholine  -> +1 (excitatory)
  gaba, glutamate -> -1 (inhibitory)
  unclear/unknown/monoamines -> +1 (default; conservative for excitation,
                                   recorded per-neuron in the manifest)
"""

import json
from pathlib import Path

import numpy as np
import pytest
from scipy import sparse

from fly.network.graph import build_signed_connectivity_matrix, nt_sign


def test_nt_sign_mapping() -> None:
    assert nt_sign("acetylcholine") == 1
    assert nt_sign("gaba") == -1
    assert nt_sign("glutamate") == -1
    assert nt_sign(None) == 1  # unknown defaults to excitatory
    assert nt_sign("unclear") == 1
    assert nt_sign("serotonin") == 1  # monoamines default excitatory


def test_signed_matrix_negates_inhibitory_edges(tmp_path: Path) -> None:
    # A (gaba) -> B: 10 synapses; C (acetylcholine) -> B: 5 synapses
    neurons = [
        {"bodyId": 1, "type": "A", "instance": "a", "nt": "gaba"},
        {"bodyId": 2, "type": "B", "instance": "b", "nt": "acetylcholine"},
        {"bodyId": 3, "type": "C", "instance": "c", "nt": "acetylcholine"},
    ]
    synapses = [
        {"source": 1, "target": 2, "weight_or_count": 10.0, "roi": "GNG"},
        {"source": 3, "target": 2, "weight_or_count": 5.0, "roi": "GNG"},
    ]

    matrix, node_ids = build_signed_connectivity_matrix(neurons, synapses)

    assert node_ids == [1, 2, 3]
    assert matrix[0, 1] == -10.0  # gaba edge negated
    assert matrix[2, 1] == 5.0    # ach edge positive


def test_signed_matrix_preserves_dedup_and_summation(tmp_path: Path) -> None:
    # per-ROI rows for one inhibitory pair: signs applied BEFORE summation
    neurons = [
        {"bodyId": 1, "type": "A", "instance": "a", "nt": "glutamate"},
        {"bodyId": 2, "type": "B", "instance": "b", "nt": "acetylcholine"},
    ]
    synapses = [
        {"source": 1, "target": 2, "weight_or_count": 10.0, "roi": "GNG"},
        {"source": 1, "target": 2, "weight_or_count": 5.0, "roi": "SMP"},
    ]

    matrix, node_ids = build_signed_connectivity_matrix(neurons, synapses)

    assert matrix[0, 1] == -15.0  # (10 + 5) * -1


def test_signed_matrix_records_unassigned_neurons(tmp_path: Path) -> None:
    neurons = [
        {"bodyId": 1, "type": "A", "instance": "a"},  # missing nt
        {"bodyId": 2, "type": "B", "instance": "b", "nt": "acetylcholine"},
    ]
    synapses = [{"source": 1, "target": 2, "weight_or_count": 3.0, "roi": "GNG"}]

    matrix, node_ids, report = build_signed_connectivity_matrix(
        neurons, synapses, return_report=True
    )

    assert matrix[0, 1] == 3.0  # unknown nt -> +1 (excitatory default)
    assert report["unknown_nt_neurons"] == [1]
