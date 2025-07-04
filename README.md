# Prometheus – The Self-Optimizing Lakehouse Engine

Unlock autonomous performance tuning and cost optimization for Databricks at any scale.

## Why Prometheus?

Spark performance tuning remains manual, error-prone and expensive. Prometheus steals the “fire” of expert knowledge and embeds it in an automated control loop that:

1. Observes every job run.
2. Diagnoses inefficiencies.
3. Writes optimisation recommendations.
4. (Optionally) rewrites the job code and opens a pull-request.

## Four Evolutionary Phases

1. **The Omen – Autonomous Observer**  
   Captures Spark event logs, extracts KPIs and writes a `prometheus_metrics` Delta table.

2. **The Oracle – Recommendation Engine**  
   Rule-based engine converts metrics into human-readable advice stored in `prometheus_recommendations`.

3. **The Titan – Autonomous Code Refactorer**  
   Parses notebook/py files with `ast` and applies fixes (e.g. `broadcast()` hints, `repartition`) automatically.

4. **The Closed Loop – CI/CD Integration**  
   Commits changes to a new branch, pushes a PR, and annotates it with before/after performance deltas.

## High-Level Architecture

```text
+-------------------+     event-log API      +--------------------+
| Databricks Jobs   |----------------------->| Event-Log Collector|
+-------------------+                        +--------------------+
                                               |
                                               v
                                        +--------------------+
                                        | Spark Event Parser |
                                        +--------------------+
                                               |
                             +-----------------+------------------+
                             | KPIs (Delta)       Logs (optional) |
                             v                                    v
+--------------------+   +--------------------+          +--------------------+
| prometheus_metrics |   | Recommendation     |          | Unity Catalog/DBFS |
+--------------------+   | Engine (rules)     |          +--------------------+
                             |                                  |
                             v                                  |
                      +--------------------+                   ...
                      | prometheus_recs   |
                      +--------------------+
                             |
                             v
                  +---------------------------+
                  | Code Refactorer (Titan)   |
                  +---------------------------+
                             |
                             v
                Git Branch / Pull-Request  (Phase 4)
```

## Repository Layout

```
prometheus/
 ├── collector/                 # Event-log downloaders
 │   └── event_log_collector.py
 ├── parser/                    # Spark-side KPIs extractor
 │   └── spark_event_parser.py
 ├── recommender/               # Rule engine (Phase 2)
 │   └── rules_engine.py
 ├── refactorer/                # AST code fixer (Phase 3)
 │   └── titan.py
 ├── jobs/                      # Databricks workflow json definitions
 ├── config.py                  # All workspace & storage config
 ├── models.py                  # Pydantic data models
 ├── main.py                    # CLI entry – runs Phase 1 end-to-end
 └── requirements.txt
```

## Getting Started (Phase 1)

1. Clone repo & install deps

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Export Databricks credentials (PAT must allow _jobs:read_, _logs:read_)

```bash
export DATABRICKS_HOST=https://<workspace-url>
export DATABRICKS_TOKEN=<personal-access-token>
```

3. Configure storage path (UC or DBFS)

```bash
export PROMETHEUS_STORAGE=abfss://lakehouse/<catalog>/prometheus
```

4. Run collector + parser locally

```bash
python -m prometheus.main --since 24h
```

This will append KPI rows to `catalog.schema.prometheus_metrics`.

## KPI Schema (`prometheus_metrics`)

| column | type | description |
|--------|------|-------------|
| run_id | bigint | Databricks run identifier |
| job_id | bigint | Parent job |
| stage_id | int | Spark stage |
| num_tasks | int | Tasks in stage |
| max_task_skew_ratio | double | `max(task_duration) / median(task_duration)` |
| total_shuffle_spill_mb | double | On-disk spill |
| broadcast_miss_flag | boolean | Heuristic for missed broadcast join |
| collected_at | timestamp | Ingestion time |

## Adding Rules (Phase 2)

Rules are Python functions that accept a KPI `Row` and return zero or more `Recommendation` objects.

```python
@rule
def skew_rule(row):
    if row.max_task_skew_ratio > 5 and row.total_shuffle_spill_mb > 1024:
        yield Recommendation(
            run_id=row.run_id,
            severity="high",
            message="Data skew detected; consider salting or enabling AQE."
        )
```

Drop rule files in `recommender/rules/`, they are auto-discovered.

## Code Refactoring (Phase 3)

`refactorer/titan.py` uses `databricks-sdk` to fetch the notebook source, converts it to an `ast.Module`, modifies nodes, and pushes back.

Implemented mutations (MVP):
• Insert `broadcast()` around small DataFrame in joins  
• Add `.repartitionByRange()` when skew detected  
• Prepend `spark.conf.set("spark.sql.adaptive.enabled", "true")` if AQE recommended

## CI/CD Loop (Phase 4)

GitHub Actions workflow `/.github/workflows/prometheus.yml`:

1. Triggered nightly or by `/optimize` comment.  
2. Spins up Prometheus container.  
3. Runs phases 1-3 on last 24h of runs.  
4. Opens PR with branch name `prometheus-opt-<date>`.

## Roadmap

- ML-driven heuristic weights (replace static rules).  
- SQL lineage analysis for better broadcast decisions.  
- Support Scala & SQL notebooks (currently Python only).  
- Web dashboard (Streamlit) for KPI & savings visualization.

## Contributing

1. Fork and create feature branch.  
2. Run `make lint test`.  
3. Open PR – describe motivation and performance gain.

## License

Apache 2.0


