from dataclasses import dataclass, asdict
from typing import Dict


@dataclass
class Tombstone:
    """Subset of performance KPI fields for Phase-1 demo."""

    run_id: int
    job_id: int
    stage_id: int
    num_tasks: int
    max_task_duration_ms: int
    median_task_duration_ms: int
    max_task_skew_ratio: float
    shuffle_read_mb: float
    shuffle_write_mb: float

    def to_dict(self) -> Dict:
        return asdict(self)
