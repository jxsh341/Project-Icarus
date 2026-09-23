"""Tests for converting canonical graph artifacts to the Shiu reference format.

The reference implementation (data/raw/reference/shiu_model.py) consumes:
- a 'completeness' CSV indexed by neuron ID, one row per neuron
- a 'connectivity' parquet with columns:
    Presynaptic_Index, Postsynaptic_Index, Excitatory x Connectivity
  where the *_Index columns are integer positions into the completeness table
  and 'Excitatory x Connectivity' is the synapse count.
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from scipy import sparse

from fly.data.reference_format import build_reference_inputs


def _artifacts(tmp_path: Path, rows, cols, data, n) -> tuple[Path, Path, Path]:
    matrix = sparse.csr_matrix((np.asarray(data, float), (rows, cols)), shape=(n, n))
    matrix.sum_duplicates()
    matrix.sort_indices()
    nodes = np.arange(1000, 1000 + n, dtype=np.int64)
    np.save(tmp_path / "connectivity_nodes.npy", nodes)
    sparse.save_npz(tmp_path / "connectivity_matrix.npz", matrix)
    return (
        tmp_path / "connectivity_nodes.npy",
        tmp_path / "connectivity_matrix.npz",
        tmp_path / "unused",
    )


def test_build_reference_inputs_maps_indices_and_counts(tmp_path: Path) -> None:
    # edge from neuron 1001 -> 1002 with 5 synapses
    nodes_path, matrix_path, _ = _artifacts(tmp_path, [1], [2], [5.0], 3)

    comp_csv, con_parquet = build_reference_inputs(nodes_path, matrix_path, tmp_path)

    df_comp = pd.read_csv(comp_csv, index_col=0)
    df_con = pd.read_parquet(con_parquet)

    assert list(df_comp.index) == [1000, 1001, 1002]
    assert list(df_con.columns) == [
        "Presynaptic_Index",
        "Postsynaptic_Index",
        "Excitatory x Connectivity",
    ]
    row = df_con.iloc[0]
    assert int(row["Presynaptic_Index"]) == 1
    assert int(row["Postsynaptic_Index"]) == 2
    assert float(row["Excitatory x Connectivity"]) == 5.0


def test_build_reference_inputs_roundtrip_matrix(tmp_path: Path) -> None:
    # build a small matrix with a duplicate-pair summation (per-ROI rows)
    nodes_path, matrix_path, _ = _artifacts(tmp_path, [0, 0, 2], [1, 1, 0], [2.0, 3.0, 4.0], 3)

    comp_csv, con_parquet = build_reference_inputs(nodes_path, matrix_path, tmp_path)

    df_con = pd.read_parquet(con_parquet)
    w = {(int(r["Presynaptic_Index"]), int(r["Postsynaptic_Index"])): float(
        r["Excitatory x Connectivity"]) for _, r in df_con.iterrows()}
    assert w[(0, 1)] == 5.0
    assert w[(2, 0)] == 4.0
    assert len(df_con) == 2


def test_build_reference_inputs_writes_manifest(tmp_path: Path) -> None:
    nodes_path, matrix_path, _ = _artifacts(tmp_path, [0], [1], [7.0], 2)

    _, _ = build_reference_inputs(nodes_path, matrix_path, tmp_path, manifest_name="ref.json")

    manifest = json.loads((tmp_path / "ref.json").read_text(encoding="utf-8"))
    assert manifest["n_neurons"] == 2
    assert manifest["n_edges"] == 1
    assert manifest["source"]["nodes"] == str(nodes_path)
    assert manifest["source"]["matrix"] == str(matrix_path)


def test_build_reference_inputs_rejects_missing_files(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        build_reference_inputs(tmp_path / "nope.npy", tmp_path / "nope.npz", tmp_path)
