# Alerting rules

## Severity model

- `warning`: service is degraded or close to SLA/risk threshold. Human attention is needed during working hours or by support team.
- `critical`: user-visible failure, data processing stopped, or dependency unavailable. Page/on-call response is required.

## Alerts

| Alert | Severity | Condition | Why it matters | Suggested action |
|---|---|---|---|---|
| Job failed | critical | `increase(batch_job_failed_total[5m]) > 0` | A CSV report failed and nomenclature may be stale. | Open job logs by `job_id`, check error code, retry if safe. |
| Job duration above SLA | warning / critical | p95 `batch_job_duration_seconds` > 30s for 2 000-row jobs during 10m; critical if > 60s. | Business target is processing 2 000 rows within 30 seconds. | Check DB latency, retry count, GCS latency, pod CPU/memory. |
| Too many skipped rows | warning | `batch_step_skip_count / batch_step_read_count > 0.01` for 10m | Data quality issue may affect warehouse reports. | Check error report, notify data owner, validate file format changes. |
| No successful jobs for N hours | critical | no increase in `batch_job_success_total` for 2h during expected load window | Pipeline may be stuck even if no single job failed. | Check pending jobs, scheduler/queue, batch service health. |
| PostgreSQL unavailable | critical | `postgres_up == 0` for 1m | Batch and ERP persistence are affected. | Escalate to DBA/platform, check DB pod/managed service/network. |
| High DB connections | warning / critical | active pool connections > 80% for 10m; > 95% for 5m critical | Batch jobs may starve ERP online traffic. | Reduce batch concurrency, inspect slow queries, scale DB/pool carefully. |
| High pod restart count | warning / critical | pod restarts increased > 3 in 15m; critical for core services | Crash loops or OOM can break processing. | Check pod events, container logs, memory limits. |
| High 5xx rate | critical | 5xx rate > 5% for 5m on monolith or batch API | Users cannot upload files or check status reliably. | Check recent deploy, dependencies, exceptions. |
| GCS access errors | critical | `increase(gcs_request_errors_total[5m]) > 0` | Files cannot be stored/read, batch processing stops. | Check credentials, IAM, bucket availability, object paths. |
| High retry rate | warning | `increase(batch_retry_total[10m]) > threshold` | Transient dependency instability is increasing. | Check DB/GCS latency and network errors. |
| Batch backlog high | warning / critical | pending jobs > threshold or oldest pending job > 15m | SLA is at risk even if jobs eventually succeed. | Scale workers or reduce concurrency bottlenecks. |
| JVM memory high | warning | heap usage > 85% for 15m | Risk of GC pauses or OOMKilled. | Check memory dashboard, heap dump if needed, tune limits. |
| Kubernetes node pressure | warning | node memory/disk pressure active | Pods may be evicted and jobs interrupted. | Add capacity or move workloads. |

## Alert routing

- `severity=critical`, `service=spring-batch-processing-service` -> SRE on-call + batch support channel.
- `severity=critical`, `service=postgresql` -> SRE on-call + DBA.
- `severity=warning`, `type=data_quality` -> data operations team.
- `severity=warning`, `type=capacity` -> platform team.

## Anti-noise rules

- Group job failure alerts by `environment`, `service`, `job_name`, `warehouse_id`.
- Do not page for each skipped row; alert on aggregate skip ratio.
- Inhibit service-level downstream alerts when `postgres_up == 0`.
- Add runbooks to every critical alert annotation.
- Use business hours routing for warning data-quality alerts unless SLA requires 24/7 response.
