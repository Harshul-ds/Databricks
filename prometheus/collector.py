"""Dummy event-log collector that just reads from local filesystem.
In real Phase-1 it would call the Databricks REST API.
"""
from __future__ import annotations

from pathlib import Path
from typing import List

from .parser import parse_event_log, Tombstone


def collect(paths: List[str | Path]) -> List[Tombstone]:
    """Collects tombstones for a list of event-log paths."""
    tombstones: List[Tombstone] = []
    for p in paths:
        tombstones.extend(parse_event_log(p))
    return tombstones
