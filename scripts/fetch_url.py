#!/usr/bin/env python3
"""Fetch a URL to a local file with headers for provenance capture."""

from __future__ import annotations

import argparse
import json
import urllib.request
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    parser.add_argument("output")
    parser.add_argument("--meta", required=True)
    args = parser.parse_args()

    request = urllib.request.Request(args.url, headers={"User-Agent": "fly-cognition/0.1"})
    with urllib.request.urlopen(request) as response:
        body = response.read()
        headers = dict(response.headers.items())
        status = getattr(response, "status", 200)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(body)

    meta = {
        "url": args.url,
        "output": str(output_path),
        "status": status,
        "headers": headers,
        "bytes": len(body),
    }
    meta_path = Path(args.meta)
    meta_path.parent.mkdir(parents=True, exist_ok=True)
    meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
