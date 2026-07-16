# Metrics catalog

| Metric name | Source | Type | Why it is needed | Example alert condition |
|---|---|---|---|---|
| `batch_job_duration_seconds` | Spring Batch Processing Service / Micrometer | SLA | Measures job processing time and SLA compliance. | p95 duration for 2 000-row jobs > 30s for 10m. |
| `batch_job_failed_total` | Spring Batch Processing Service | Business/SLA | Counts failed batch jobs. | increase over 5m > 0 for critical warehouses. |
| `batch_job_success_total` | Spring Batch Processing Service | Business | Counts successful jobs and proves pipeline is working. | no increase for N hours during business window. |
| `batch_step_read_count` | Spring Batch step metrics | Technical/Business | Shows how many rows were read from CSV. | read count is 0 for completed job with non-empty file. |
| `batch_step_write_count` | Spring Batch step metrics | Technical/Business | Shows how many rows were written to nomenclature DB. | write/read ratio below expected threshold. |
| `batch_step_skip_count` | Spring Batch step metrics | Business/SLA | Tracks skipped bad rows. | skipped rows > 1% of read rows for 10m. |
| `batch_retry_total` | Spring Batch Processing Service | Technical | Detects transient failures and unstable dependencies. | retries increase rapidly for 10m. |
| `uploaded_files_total` | Java/WildFly Monolith | Business | Tracks upload volume by warehouse/time. | sudden drop to zero during expected upload window. |
| `rows_processed_total` | Spring Batch Processing Service | Business | Tracks throughput and daily volume. | rows/sec below required baseline for 15m. |
| `rows_failed_total` | Spring Batch Processing Service | Business/SLA | Tracks invalid or failed rows. | failed rows > threshold by warehouse or file type. |
| `processing_sla_violation_total` | Spring Batch Processing Service | SLA | Counts reports that missed the 30s target for 2 000 rows. | any increase for high-priority warehouses. |
| `http_server_requests_seconds` | Monolith and Spring Boot Actuator | Technical/SLA | Measures HTTP latency and request rates. | p95 upload/status API latency > 1s for 10m. |
| `jvm_memory_used_bytes` | JVM / Micrometer / JMX Exporter | Technical | Detects memory pressure and leaks. | heap used > 85% for 15m. |
| `db_connection_pool_active` | HikariCP/Micrometer or app pool metrics | Technical | Detects DB pool saturation. | active connections > 80% of max for 10m. |
| `postgres_up` | PostgreSQL Exporter | Technical/SLA | Checks PostgreSQL availability. | equals 0 for 1m. |
| `kube_pod_container_status_restarts_total` | kube-state-metrics | Technical | Detects pod restarts and crash loops. | increase > 3 in 15m for critical pods. |
| `kube_pod_status_phase` | kube-state-metrics | Technical | Tracks pods pending/failed/running. | pod stuck Pending for > 10m. |
| `container_cpu_usage_seconds_total` | cAdvisor/kubelet | Technical | Detects CPU saturation. | CPU usage near limit for 15m. |
| `container_memory_working_set_bytes` | cAdvisor/kubelet | Technical | Detects memory pressure. | memory usage > 90% of limit for 10m. |
| `gcs_request_errors_total` | Monolith / Batch Service | Technical/SLA | Detects GCS read/write/access errors. | increase > 0 for 5m. |
| `batch_active_jobs` | Spring Batch Processing Service | Technical/Business | Tracks currently running jobs. | active jobs > configured safe parallelism. |
| `batch_pending_jobs` | Batch job queue/status store | SLA | Detects backlog. | pending jobs age > 15m or queue depth > threshold. |
| `batch_job_rows_per_second` | Spring Batch Processing Service | SLA | Measures processing throughput. | below baseline for 15m with active jobs. |
| `postgres_locks_count` | PostgreSQL Exporter/custom query | Technical | Detects contention caused by batch writes. | locks above baseline for 10m. |
| `postgres_deadlocks_total` | PostgreSQL Exporter | Technical/SLA | Detects write conflicts. | increase > 0 in 5m. |

## Notes on labels

Recommended metric labels:

- `service`;
- `environment`;
- `job_name`;
- `step_name`;
- `status`;
- `warehouse_id` only if number of warehouses is controlled;
- `file_type`;
- `exception` for bounded exception classes.

Avoid high-cardinality labels in Prometheus:

- `job_id`;
- `file_id`;
- raw `trace_id`;
- user id;
- file name.

Use these identifiers in logs and traces instead.
