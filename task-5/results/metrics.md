# Каталог метрик

| Имя метрики | Источник | Тип | Зачем нужна | Пример условия алерта |
|---|---|---|---|---|
| `batch_job_duration_seconds` | Spring Batch Processing Service / Micrometer | SLA | Измеряет время обработки job и соблюдение SLA. | p95 duration для jobs на 2 000 строк > 30s в течение 10m. |
| `batch_job_failed_total` | Spring Batch Processing Service | Бизнес/SLA | Считает неуспешные batch jobs. | прирост за 5m > 0 для критичных складов. |
| `batch_job_success_total` | Spring Batch Processing Service | Бизнес | Считает успешные jobs и подтверждает работу пайплайна. | нет прироста за N часов в рабочем окне. |
| `batch_step_read_count` | Spring Batch step metrics | Техническая/бизнес | Показывает, сколько строк прочитано из CSV. | read count равен 0 для completed job с непустым файлом. |
| `batch_step_write_count` | Spring Batch step metrics | Техническая/бизнес | Показывает, сколько строк записано в nomenclature DB. | write/read ratio ниже ожидаемого порога. |
| `batch_step_skip_count` | Spring Batch step metrics | Бизнес/SLA | Отслеживает пропущенные ошибочные строки. | skipped rows > 1% от read rows за 10m. |
| `batch_retry_total` | Spring Batch Processing Service | Техническая | Выявляет временные ошибки и нестабильные зависимости. | retries быстро растут в течение 10m. |
| `uploaded_files_total` | Java/WildFly Monolith | Бизнес | Отслеживает объём загрузок по складу и времени. | внезапное падение до нуля в ожидаемом окне загрузок. |
| `rows_processed_total` | Spring Batch Processing Service | Бизнес | Отслеживает throughput и дневной объём. | rows/sec ниже базового уровня в течение 15m. |
| `rows_failed_total` | Spring Batch Processing Service | Бизнес/SLA | Отслеживает невалидные или неуспешно обработанные rows. | failed rows выше порога по складу или типу файла. |
| `processing_sla_violation_total` | Spring Batch Processing Service | SLA | Считает отчёты, которые не уложились в целевые 30s для 2 000 строк. | любой прирост для складов с высоким приоритетом. |
| `http_server_requests_seconds` | Monolith и Spring Boot Actuator | Техническая/SLA | Измеряет HTTP latency и request rate. | p95 upload/status API latency > 1s в течение 10m. |
| `jvm_memory_used_bytes` | JVM / Micrometer / JMX Exporter | Техническая | Выявляет memory pressure и утечки. | heap used > 85% в течение 15m. |
| `db_connection_pool_active` | HikariCP/Micrometer или метрики app pool | Техническая | Выявляет насыщение DB pool. | active connections > 80% от max в течение 10m. |
| `postgres_up` | PostgreSQL Exporter | Техническая/SLA | Проверяет доступность PostgreSQL. | равно 0 в течение 1m. |
| `kube_pod_container_status_restarts_total` | kube-state-metrics | Техническая | Выявляет pod restarts и crash loops. | increase > 3 за 15m для критичных pods. |
| `kube_pod_status_phase` | kube-state-metrics | Техническая | Отслеживает состояния pods: pending/failed/running. | pod находится в Pending больше 10m. |
| `container_cpu_usage_seconds_total` | cAdvisor/kubelet | Техническая | Выявляет CPU saturation. | CPU usage близко к limit в течение 15m. |
| `container_memory_working_set_bytes` | cAdvisor/kubelet | Техническая | Выявляет memory pressure. | memory usage > 90% от limit в течение 10m. |
| `gcs_request_errors_total` | Monolith / Batch Service | Техническая/SLA | Выявляет ошибки чтения/записи/доступа к GCS. | increase > 0 за 5m. |
| `batch_active_jobs` | Spring Batch Processing Service | Техническая/бизнес | Отслеживает текущие running jobs. | active jobs > безопасного уровня parallelism. |
| `batch_pending_jobs` | Batch job queue/status store | SLA | Выявляет backlog. | возраст pending jobs > 15m или queue depth выше порога. |
| `batch_job_rows_per_second` | Spring Batch Processing Service | SLA | Измеряет throughput обработки. | ниже baseline в течение 15m при наличии active jobs. |
| `postgres_locks_count` | PostgreSQL Exporter/custom query | Техническая | Выявляет contention от batch writes. | locks выше baseline в течение 10m. |
| `postgres_deadlocks_total` | PostgreSQL Exporter | Техническая/SLA | Выявляет write conflicts. | increase > 0 за 5m. |

## Примечания по labels

Рекомендуемые labels для метрик:

- `service`;
- `environment`;
- `job_name`;
- `step_name`;
- `status`;
- `warehouse_id` только если количество складов контролируемо;
- `file_type`;
- `exception` для ограниченного набора классов исключений.

Избегать high-cardinality labels в Prometheus:

- `job_id`;
- `file_id`;
- raw `trace_id`;
- user id;
- file name.

Эти идентификаторы лучше использовать в logs и traces.
