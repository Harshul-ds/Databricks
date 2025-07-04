"""Spark Event Log parser – Phase 1 minimal implementation.

For demo purposes we assume the event log is a JSON file containing a list of
Spark listener event dicts (heavily simplified relative to the real format).
"""
from __future__ import annotations

import json
import statistics
from pathlib import Path
from typing import List, Dict

from .models import Tombstone


def _mb(bytes_val: int) -> float:
    """Convert bytes to MB with 1-decimal precision."""
    return round(bytes_val / (1024 * 1024), 1)


def parse_event_log(file_path: str | Path) -> List[Tombstone]:
    """Parse a simplified Spark event-log JSON file into KPI tombstones.

    Parameters
    ----------
    file_path: str | Path
        Path to JSON file containing a list of event dicts.
    """
    path = Path(file_path)
    events: List[Dict] = json.loads(path.read_text())

    # Group TaskEnd events by stageId
    stages: Dict[int, List[Dict]] = {}
    for ev in events:
        if ev.get("Event") == "SparkListenerTaskEnd":
            stage_id = ev["Stage ID"]
            stages.setdefault(stage_id, []).append(ev)

    tombstones: List[Tombstone] = []
    for stage_id, tasks in stages.items():
        durations = [t["Task Info"]["Duration"] for t in tasks]
        reads = sum(t["Task Metrics"].get("Shuffle Read Bytes", 0) for t in tasks)
        writes = sum(t["Task Metrics"].get("Shuffle Write Bytes", 0) for t in tasks)
        num_tasks = len(tasks)
        max_dur = max(durations)
        median_dur = int(statistics.median(durations))
        skew_ratio = round(max_dur / median_dur if median_dur else 0, 2)

        tombstones.append(
            Tombstone(
                run_id=1,  # dummy for demo
                job_id=1,  # dummy
                stage_id=stage_id,
                num_tasks=num_tasks,
                max_task_duration_ms=max_dur,
                median_task_duration_ms=median_dur,
                max_task_skew_ratio=skew_ratio,
                shuffle_read_mb=_mb(reads),
                shuffle_write_mb=_mb(writes),
            )
        )
    return tombstones
