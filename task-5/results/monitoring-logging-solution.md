# Monitoring and logging solution for TradeWare

## Цель

TradeWare нужно перейти от файловых логов и базового VM/WildFly мониторинга к централизованной observability-платформе. Цель решения:

- контролировать ERP-монолит, Spring Batch Processing Service, PostgreSQL, GCS и Kubernetes;
- выдерживать рост нагрузки и 100-150 параллельных загрузок CSV;
- отслеживать SLA обработки отчета на 2 000 строк до 30 секунд;
- быстро находить причины ошибок через метрики, логи, job/file identifiers и traces;
- получать оповещения до того, как деградация становится массовой.

## Выбранный стек

- **Prometheus** - сбор time-series метрик.
- **Grafana** - дашборды и визуализация SLI/SLA.
- **Alertmanager** - маршрутизация и дедупликация алертов.
- **Micrometer + Spring Boot Actuator** - метрики Spring Batch Processing Service.
- **PostgreSQL Exporter** - метрики PostgreSQL.
- **kube-state-metrics / node-exporter / cAdvisor** - метрики Kubernetes, nodes, containers.
- **Fluent Bit или Filebeat** - сбор container logs.
- **Elasticsearch или OpenSearch + Kibana/OpenSearch Dashboards** - централизованное хранение и поиск логов.

## Metrics architecture

### Spring Batch Processing Service

Spring Batch сервис публикует метрики через Micrometer и Spring Boot Actuator endpoint:

```text
/actuator/prometheus
```

Метрики включают:

- длительность batch job;
- успешные и failed job;
- read/write/skip counters;
- retry counters;
- количество обработанных и ошибочных строк;
- SLA violations;
- HTTP metrics;
- JVM metrics;
- connection pool metrics.

Ключевые labels:

- `service`;
- `environment`;
- `job_name`;
- `step_name`;
- `status`;
- `warehouse_id`;
- `file_type`.

Высококардинальные значения вроде `job_id` и `file_id` не стоит добавлять во все Prometheus labels. Их лучше хранить в логах и traces. В метрики можно добавлять только тогда, когда cardinality контролируема или используется отдельная exemplars/tracing интеграция.

### Java/WildFly Monolith

Монолит должен публиковать:

- HTTP latency и 5xx rate по ERP API;
- количество загруженных файлов;
- ошибки загрузки в GCS;
- размер очереди/количество активных batch requests;
- JVM и connection pool metrics.

Если монолит нельзя быстро перевести на Micrometer, можно использовать:

- JMX Exporter;
- WildFly/JBoss metrics subsystem;
- sidecar exporter.

### PostgreSQL

PostgreSQL Exporter собирает:

- `postgres_up`;
- активные подключения;
- locks;
- transaction rate;
- query duration по возможности через `pg_stat_statements`;
- replication/storage metrics, если применимо.

Для TradeWare особенно важны DB connection pool и нагрузка от batch jobs, потому что параллельная обработка CSV может конкурировать с online ERP-трафиком.

### Kubernetes infrastructure

Kubernetes-метрики собираются через:

- kube-state-metrics: состояние deployments, pods, jobs, cronjobs, restarts;
- node-exporter: CPU, memory, disk, network nodes;
- cAdvisor/kubelet: container CPU/memory/restarts/filesystem.

Эти метрики нужны для диагностики OOMKilled, CrashLoopBackOff, throttling, насыщения node resources и проблем autoscaling.

## Prometheus scraping

Prometheus scrape-ит targets:

- `batch-processing-service:8080/actuator/prometheus`;
- `monolith:8080/metrics` или `/actuator/prometheus`;
- `postgres-exporter:9187/metrics`;
- Kubernetes endpoints через service discovery.

В production Kubernetes лучше использовать Prometheus Operator и `ServiceMonitor`, но для проектного задания достаточно показать scrape-конфигурацию в [prometheus/prometheus.yml](prometheus/prometheus.yml).

## Grafana dashboards

Grafana строит несколько групп дашбордов:

### Executive / SLA dashboard

- количество загруженных файлов за час/день;
- success/failure rate batch jobs;
- p95/p99 длительность обработки;
- SLA violations;
- rows processed / rows failed;
- top warehouses by failures.

### Batch operations dashboard

- активные jobs;
- job duration by status;
- step read/write/skip counters;
- retry rate;
- failed jobs by error code;
- queue depth или pending uploads;
- throughput rows/sec.

### Application dashboard

- ERP HTTP latency;
- 5xx rate;
- JVM heap/non-heap;
- GC pauses;
- active DB connections;
- thread pool utilization.

### PostgreSQL dashboard

- `postgres_up`;
- active connections;
- slow queries;
- locks;
- transaction throughput;
- CPU/memory/disk saturation;
- deadlocks and conflicts.

### Kubernetes dashboard

- pod restarts;
- pod readiness;
- CPU/memory requests vs usage;
- container OOMKilled;
- node pressure;
- job pod lifecycle.

## Alertmanager

Prometheus evaluates alert rules and sends firing alerts to Alertmanager. Alertmanager:

- groups related alerts by `service`, `severity`, `environment`;
- deduplicates repeated events;
- applies inhibition, for example suppress service-level alerts when PostgreSQL is down;
- routes notifications to Slack/Teams/email/PagerDuty;
- sends critical alerts to on-call SRE/platform team;
- sends warning alerts to application support or data operations.

Example routing:

- `severity=critical` -> on-call channel + paging;
- `severity=warning` -> team chat + ticket;
- batch data quality alerts -> data operations channel;
- infrastructure alerts -> platform/SRE channel.

## Logging architecture

Applications write structured JSON logs to stdout/stderr. Kubernetes container runtime stores logs on nodes. Fluent Bit/Filebeat runs as DaemonSet and:

1. tails container log files;
2. enriches records with Kubernetes metadata: namespace, pod, container, labels;
3. parses JSON payload;
4. sends logs to Elasticsearch/OpenSearch.

Kibana/OpenSearch Dashboards is used for:

- search by `job_id`, `file_id`, `warehouse_id`, `trace_id`;
- filtering failed jobs by `error_code`;
- dashboards for error trends;
- support investigations and incident reviews.

## Correlation: job_id, file_id, trace_id

Every upload should generate stable identifiers:

- `file_id` - unique uploaded file identifier;
- `job_id` - Spring Batch job execution id or domain job id;
- `warehouse_id` - warehouse/business context;
- `trace_id` - distributed trace id for request/job creation flow;
- `span_id` - current operation span id.

Recommended flow:

1. Angular sends upload request.
2. Monolith creates `file_id` and persists upload metadata.
3. Monolith stores CSV in GCS.
4. Monolith creates batch job and passes `file_id`, `warehouse_id`, `trace_id`.
5. Spring Batch stores `job_id` and uses MDC/log context for all logs.
6. Logs contain `job_id`, `file_id`, `warehouse_id`, `trace_id`.
7. Metrics contain low-cardinality labels and link to logs through dashboard variables or exemplars where supported.

This gives operators a fast path:

```text
Alert -> Grafana panel -> failing service/job -> Kibana query by job_id/file_id/trace_id -> root cause
```

## Operational outcome

The proposed stack gives TradeWare:

- visibility into batch SLA and throughput;
- early detection of failed jobs and DB pressure;
- centralized structured logs instead of scattered files;
- correlation across monolith, batch service, PostgreSQL and GCS;
- an observability base suitable for migration toward microservices and Kubernetes/cloud infrastructure.
