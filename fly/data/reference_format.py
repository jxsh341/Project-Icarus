"""Convert canonical graph artifacts to the Shiu reference input format.

The reference implementation (data/raw/reference/shiu_model.py, create_model())
consumes two files:

- a "completeness" CSV, one row per neuron, indexed by biological neuron ID;
- a "connectivity" parquet with columns
    Presynaptic_Index, Postsynaptic_Index, Excitatory x Connectivity
  where the index columns are 0-based positions into the completeness table
  and the weight column is the synapse count between the pair.

This module adapts FLY-BASE canonical artifacts (connectivity_nodes.npy +
connectivity_matrix.npz) to that format without altering any values.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import sparse


def build_reference_inputs(
    nodes_path: Path,
    matrix_path: Path,
    output_dir: Path,
    comp_name: str = "completeness.csv",
    con_name: str = "connectivity.parquet",
    manifest_name: str | None = None,
) -> tuple[Path, Path]:
    """Write Shiu-format completeness/connectivity files from canonical artifacts.

    Returns (path_to_comp_csv, path_to_con_parquet).
    """
    nodes_path = Path(nodes_path)
    matrix_path = Path(matrix_path)
    if not nodes_path.is_file():
        raise FileNotFoundError(nodes_path)
    if not matrix_path.is_file():
        raise FileNotFoundError(matrix_path)

    node_ids = np.load(nodes_path).tolist()
    matrix = sparse.load_npz(matrix_path).tocsr()
    if matrix.shape != (len(node_ids), len(node_ids)):
        raise ValueError(
            f"matrix shape {matrix.shape} does not match {len(node_ids)} node ids"
        )

    coo = matrix.tocoo()
    df_comp = pd.DataFrame(index=pd.Index(node_ids, name="root_id"))
    df_comp["included"] = True

    df_con = pd.DataFrame(
        {
            "Presynaptic_Index": coo.row.astype(np.int64),
            "Postsynaptic_Index": coo.col.astype(np.int64),
            "Excitatory x Connectivity": coo.data.astype(float),
        }
    )

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    comp_path = output_dir / comp_name
    con_path = output_dir / con_name
    df_comp.to_csv(comp_path)
    df_con.to_parquet(con_path)

    if manifest_name:
        manifest = {
            "n_neurons": int(len(node_ids)),
            "n_edges": int(matrix.nnz),
            "format": "shiu-reference (create_model inputs)",
            "source": {
                "nodes": str(nodes_path),
                "matrix": str(matrix_path),
            },
            "outputs": {
                "completeness": str(comp_path),
                "connectivity": str(con_path),
            },
        }
        (output_dir / manifest_name).write_text(
            json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
        )

    return comp_path, con_path
