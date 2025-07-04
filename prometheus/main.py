"""CLI entry point for Prometheus Phase-1 demo."""
from __future__ import annotations

import argparse
from pathlib import Path
import json

from .collector import collect


def _parse_args():
    p = argparse.ArgumentParser(description="Prometheus – Phase-1 event-log parser")
    p.add_argument("event_logs", nargs="+", help="Path(s) to Spark event-log JSON files")
    p.add_argument("--output", "-o", default="tombstones.json", help="Output JSON path")
    return p.parse_args()


def main():
    args = _parse_args()
    tombstones = collect(args.event_logs)
    out_path = Path(args.output)
    out_path.write_text(json.dumps([t.to_dict() for t in tombstones], indent=2))
    print(f"Wrote {len(tombstones)} tombstone(s) to {out_path.resolve()}")


if __name__ == "__main__":
    main()
