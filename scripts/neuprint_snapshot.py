"""neuPrint snapshot CLI for batch-fetching and local materialization."""

from __future__ import annotations

import argparse
from pathlib import Path

from fly.data.loader import NeuPrintSnapshotConfig, NeuPrintStreamingLoader, ensure_neuprint_token


def read_token_file(path: Path) -> str:
    token = path.read_text(encoding="utf-8").strip()
    if not token:
        raise RuntimeError(f"Token file is empty: {path}")
    return token


class DeferredNeuPrintClient:
    def __init__(self, server: str, dataset: str, token: str) -> None:
        from neuprint import Client, fetch_adjacencies, fetch_neurons

        self._client = Client(server, dataset=dataset, token=token)
        self._fetch_adjacencies = fetch_adjacencies
        self._fetch_neurons = fetch_neurons

    def fetch_neurons(self, body_ids: list[int]) -> list[dict]:
        neurons_df, _ = self._fetch_neurons(body_ids, client=self._client)
        return neurons_df.to_dict(orient="records")

    def fetch_adjacencies(self, body_ids: list[int], direction: str = "outgoing") -> list[dict]:
        if direction == "incoming":
            _, edges_df = self._fetch_adjacencies(None, body_ids, client=self._client)
        else:
            _, edges_df = self._fetch_adjacencies(body_ids, None, client=self._client)
        return edges_df.to_dict(orient="records")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--server", default="https://neuprint.janelia.org")
    parser.add_argument("--snapshot-dir", required=True)
    parser.add_argument("--batch-size", type=int, default=500)
    parser.add_argument("--token")
    parser.add_argument("--token-file")
    parser.add_argument("--body-ids", required=True, help="Comma-separated body IDs")
    parser.add_argument(
        "--mode",
        choices=["neurons", "adjacencies", "both", "closed-subgraph", "incoming"],
        default="both",
    )
    args = parser.parse_args()

    if args.token_file:
        token = read_token_file(Path(args.token_file))
    else:
        token = ensure_neuprint_token(explicit_token=args.token)
    body_ids = [int(value) for value in args.body_ids.split(",") if value.strip()]
    config = NeuPrintSnapshotConfig(
        dataset=args.dataset,
        batch_size=args.batch_size,
        snapshot_dir=Path(args.snapshot_dir),
        server=args.server,
    )
    client = DeferredNeuPrintClient(server=args.server, dataset=args.dataset, token=token)
    loader = NeuPrintStreamingLoader(config, client=client)

    if args.mode in {"neurons", "both"}:
        loader.snapshot_neurons(body_ids)
    if args.mode in {"adjacencies", "both"}:
        loader.snapshot_adjacencies(body_ids)
    if args.mode == "incoming":
        loader.snapshot_adjacencies(body_ids, direction="incoming")
    if args.mode == "closed-subgraph":
        loader.snapshot_closed_subgraph(body_ids)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
