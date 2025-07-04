"""Simple unit test for the Phase-1 parser using pytest."""
from pathlib import Path

from prometheus.parser import parse_event_log


def test_parse_event_log(tmp_path):
    # Copy sample event log into temp dir to simulate external file
    sample = (Path(__file__).parent / "sample_event_log.json").resolve()
    dest = tmp_path / "event.json"
    dest.write_bytes(sample.read_bytes())

    tombstones = parse_event_log(dest)
    # We expect 2 stages in sample log
    assert len(tombstones) == 2

    # Validate fields of first tombstone
    t0 = tombstones[0]
    assert t0.stage_id == 0
    assert t0.num_tasks == 2
    assert t0.max_task_duration_ms == 120
    assert t0.median_task_duration_ms == 105  # median(120, 90)
    assert t0.shuffle_read_mb > 0
