# Databricks Field Manual


## 1. Workspaces & Accounts  
A **workspace** is an isolated compute / metadata plane accessible via a unique URL (e.g. `https://acme.cloud.databricks.com`). An **account** may own multiple workspaces; it also owns Unity Catalog and billing.

*Key APIs & Docs*  
– Account console docs: <https://docs.databricks.com/administration-guide/account-settings/index.html>  
– Workspace API root: `https://<workspace>/api/`

Implementation Tips  
1. PAT token + host URL in env vars → `databricks-sdk` auto-discovers.  
2. Most REST resources are _workspace-scoped_; Unity-Catalog objects are _account-scoped_.

---

## 2. Clusters, SQL Warehouses & Compute Policies
See official setup: <https://docs.databricks.com/clusters/index.html>

| Concept | What | When to use |
|---------|------|-------------|
| **Job Cluster** | Ephemeral; defined inside a Job JSON | Dedicated resources, full isolation |
| **All-Purpose Cluster** | Interactive notebooks | Ad-hoc exploration or scheduled analytics |
| **SQL Warehouse** | Serverless / classic; Photon-powered | BI dashboards & JDBC apps |
| **Policy** | JSON constraints on clusters | Control cost & enforce security |

Example payload (create via Jobs API):
```json
"new_cluster": {
  "spark_version": "14.3.x-scala2.12",
  "node_type_id": "i3.xlarge",
  "autoscale": {"min_workers": 2, "max_workers": 8},
  "policy_id": "restrict-i3"
}
```

Docs: <https://docs.databricks.com/clusters/policies.html>

---

## 3. Jobs & Workflows
Docs: <https://docs.databricks.com/workflows/jobs/index.html>

REST flow (v2.1):
1. Create job: `POST /jobs/create` → returns `job_id`.  
2. Trigger run: `POST /jobs/run-now` with params → `run_id`.  
3. Poll run: `GET /jobs/runs/get?run_id=...`.

Prometheus Phase-1 lists finished runs via `GET /jobs/runs/list?completed_only=true`.

---

## 4. Spark Event Logs
Docs: <https://docs.databricks.com/compute/spark-eventlogs.html>

• JSON / GZ files capturing every `SparkListener*` event.  
• Prometheus parses `SparkListenerTaskEnd` to compute aggregates like `max_task_skew_ratio`.

Event-log download pattern:
```python
w = WorkspaceClient()
run = w.jobs.get_run(run_id)
log_path = run.run_page_url + "/spark-monitor"  # embedded link
```

---

## 5. Delta Lake
Docs: <https://docs.delta.io/latest/index.html>

Important commands: `OPTIMIZE`, `VACUUM`, `ZORDER`, time-travel.  
Prometheus Oracle flags sub-optimal file sizes and suggests `OPTIMIZE`.

---

## 6. Unity Catalog (UC)
Docs: <https://docs.databricks.com/data-governance/unity-catalog/index.html>

Hierarchy: **catalog ▶ schema ▶ table**. Managed by account admin.  
Attach cluster with `spark.databricks.unityCatalog.enabled true` (default ≥ 13.x).

---

## 7. Databricks Repos
Docs: <https://docs.databricks.com/repos/index.html>

Key endpoints:
```http
POST /api/2.0/repos      # clone
PATCH /api/2.0/repos/{id}  # create commit, switch branch
```
Prometheus Titan fetches notebook source via Repos API, alters AST, pushes branch.

---

## 8. Libraries & Init Scripts
Docs: <https://docs.databricks.com/clusters/libraries.html>

• Wheel/Jar install at cluster create or via DBFS.  
• Init scripts run on every node boot (`/databricks/init/`).

---

## 9. Databricks SQL, Photon & Serverless
Docs: <https://docs.databricks.com/sql/index.html>

• Photon = vectorized C++ engine. Auto-enabled on SQL Warehouses and DBR ≥ 12.2.  
• Serverless warehouses = instant, per-query billing.

---

## 10. Storage: DBFS, Volumes, External Locations
Docs: <https://docs.databricks.com/storage/index.html>

| Layer | Purpose |
|-------|---------|
| **DBFS** | Default mount (`dbfs:/`) for notebooks, logs |
| **Volumes** | UC-managed pointers to cloud buckets |
| **External Location** | Defines path + ownership for Delta tables |

Prometheus metrics table can live in a UC volume to inherit RBAC.

---

## 11. Secrets, Tokens, SCIM
Docs: <https://docs.databricks.com/administration-guide/secrets/index.html>

• Store API keys in `databricks secrets`.  
• Provision users/groups via SCIM: `POST /preview/scim/v2/Users`.

---

## 12. SDKs & Rate Limits
Docs: <https://docs.databricks.com/dev-tools/sdk-python.html>

Python SDK auto-retries & paginates. Rate limit ≈30req/s per workspace.

---

## 13. Spark-SQL Optimizer & AQE
Docs: <https://spark.apache.org/docs/latest/sql-performance.html#adaptive-query-execution>

Useful flags Prometheus may toggle:
```sql
SET spark.sql.adaptive.enabled = true;
SET spark.sql.shuffle.partitions = 200;
```

---

## 14. Monitoring & Cost Usage
Docs: <https://docs.databricks.com/administration-guide/account-settings/usage.html>

• Billable usage logs land daily in cloud storage.  
• Combine with Prometheus KPIs to show $ savings.

---

## 15. Databricks Connect v2
Docs: <https://docs.databricks.com/dev-tools/databricks-connect.html>

Run Spark code locally against remote cluster – perfect for unit tests.

---

# Appendix – Deep-Dive Topics

## A1. Spark Programming Abstractions

| Abstraction | What it is | When to use |
|-------------|------------|-------------|
| **RDD (Resilient Distributed Dataset)** | Low-level, immutable distributed collection of JVM objects. Provides explicit transformation (`map`, `flatMap`, `reduceByKey`, …) and action APIs. | Fine-grained control, custom partitioning, calling non-SQL/typed functions, or when you need to maintain lineage for fault tolerance. |
| **DataFrame** | Distributed table backed by Catalyst logical/physical plans. Columnar; lazily optimized. Supports SQL, Python, Scala, Java. | Almost always the default for ETL, analytics, ML feature prep. |
| **Dataset** (Scala/Java only) | Typed DataFrame (`Dataset[CaseClass]`) with compile-time type safety and object encoders. | When you need both static typing and Catalyst optimizations. |

Rule of thumb: start with DataFrame; drop to RDDs for custom algorithms or when you need per-element control (e.g., graph algorithms, deep nested parsing).

## A2. Execution Flow (Driver → DAG → Tasks)
1. **Transformation building** – Your code builds a logical plan (lazy).
2. **Catalyst optimization** – Rules prune projections, push predicates, collapse filters.
3. **Physical planning** – Multiple physical plans are costed; cheapest wins.
4. **DAG Scheduler** – Logical plan → stages separated by shuffle boundaries.
5. **Task Scheduler** – Launches tasks on executors via cluster manager.
6. **Execution & Shuffle** – Intermediate data written to disk/network; `ShuffleManager` handles sort/hash.
7. **Result handling** – Driver fetches action results, materializes DataFrame, or writes to sink.

Key configs to tune:
```conf
spark.sql.shuffle.partitions   # default 200; adjust ↓ for small data, ↑ for huge joins
spark.sql.adaptive.enabled     # turn on AQE (Adaptive Query Execution)
```

## A3. Partitioning & Data Skew
• Partitions should be sized 100-512 MB for optimal shuffle.  
• Use `repartition(col)` or `repartitionByRange()` for even key distribution.  
• Severe skew symptoms: single task 10× slower, spill to disk, executor timeout.

Mitigations: salting keys, auto-skew join (`spark.sql.adaptive.skewJoin.enabled`), broadcast small side.

## A4. Shuffle Mechanics
Shuffle writes map-side output to local disks, creates index files, notifies driver; reduce tasks pull using Netty.

Tuning flags:
```
spark.shuffle.compress true
spark.reducer.maxSizeInFlight 48m
spark.shuffle.spill true
```

## A5. Broadcast Variables & Accumulators
| Feature | Purpose |
|---------|---------|
| **Broadcast variable** | Ship a read-only value (lookup table, model weights) once per executor. Use `broadcast(df)` or `sc.broadcast(obj)` |
| **Accumulator** | Distributed write-only counter used for instrumentation (e.g., malformed rows).|

AQE can auto-decide broadcast joins when one side < 10% shuffle threshold.

## A6. Caching & Persistence
`df.cache()` uses in-memory columnar cache (off-heap in Photon).  
Storage levels: `MEMORY_ONLY`, `MEMORY_AND_DISK`, `DISK_ONLY`, `OFF_HEAP`.

Tip: always `count()` after `cache()` in interactive workflows to trigger materialization.

## A7. Checkpointing & Lineage Truncation
For long lineage chains (>100 transformations) or iterative algorithms, call `sc.setCheckpointDir("dbfs:/checkpoints")` and `rdd.checkpoint()` to avoid stack overflows and huge DAGs.

## A8. Tungsten & Whole-Stage Codegen
Spark 2+ rewrote physical engine to generate Java bytecode that directly manipulates binary rows. Yields big gains in CPU & GC. Enabled by default; tune via `spark.sql.codegen.wholeStage`.

Photon (Databricks) replaces this Java layer with vectorized C++ for DataFrame/SQL paths.

## A9. Delta Lake Internals (extra detail)
• **_delta_log** JSON → PARQUET checkpoint every n commits.  
• **OPTIMIZE** uses bin-packing; picks files < 128 MB.  
• **ZORDER** builds locality maps, rewriting files to cluster columns.

Isolation levels:
| Operation | Locking/Transaction |
|-----------|--------------------|
| Read | Snapshot-isolation via version ID |
| Write | Optimistic concurrency; commit fails on overlapping writes |

## A10. Unity Catalog Security Model
| Level | Principal | Grants |
|-------|-----------|--------|
| Catalog | account-level admin | `USE CATALOG` |
| Schema | workspace groups | `CREATE TABLE`, `USAGE` |
| Table  | workspace groups | `SELECT`, `MODIFY` |

All grants are audited via system tables (`system.access`).

## A11. Monitoring Stack
• **Ganglia UI** → executor metrics (heap, CPU).  
• **Spark UI** → per-stage times, shuffle spill, skew visualization.  
• **Databricks metrics API** → scrapeable Prometheus endpoint (`/metrics`).  
• **Billable Usage Logs** → raw DBU, node hours, photon hours.

## Further Reading
1. *Spark: The Definitive Guide* – Chambers & Zaharia.  
2. *Delta Lake Internals* – Venkatesh & Sale.

