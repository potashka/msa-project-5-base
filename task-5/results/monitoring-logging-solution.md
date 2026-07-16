# Решение по мониторингу и логированию для TradeWare

## Цель

TradeWare нужно перейти от файловых логов и базового VM/WildFly мониторинга к централизованной observability-платформе. Цель решения:

- контролировать ERP-монолит, Spring Batch Processing Service, PostgreSQL, GCS и Kubernetes;
- выдерживать рост нагрузки и 100-150 параллельных загрузок CSV;
- отслеживать SLA обработки отчёта на 2 000 строк до 30 секунд;
- быстро находить причины ошибок через метрики, логи, идентификаторы `job_id`/`file_id` и traces;
- получать оповещения до того, как деградация становится массовой.

## Выбранный стек

- **Prometheus** - сбор метрик временных рядов.
- **Grafana** - дашборды и визуализация SLI/SLA.
- **Alertmanager** - маршрутизация и дедупликация алертов.
- **Micrometer + Spring Boot Actuator** - метрики Spring Batch Processing Service.
- **PostgreSQL Exporter** - метрики PostgreSQL.
- **kube-state-metrics / node-exporter / cAdvisor** - метрики узлов и контейнеров Kubernetes.
- **Fluent Bit или Filebeat** - сбор контейнерных логов.
- **Elasticsearch или OpenSearch + Kibana/OpenSearch Dashboards** - централизованное хранение и поиск логов.

## Архитектура метрик

### Spring Batch Processing Service

Spring Batch сервис публикует метрики через Micrometer и Spring Boot Actuator endpoint:

```text
/actuator/prometheus
```

Метрики включают:

- длительность batch job;
- успешные и неуспешные jobs;
- счётчики read/write/skip;
- счётчики retry;
- количество обработанных и ошибочных строк;
- нарушения SLA;
- HTTP-метрики;
- JVM-метрики;
- метрики connection pool.

Ключевые labels:

- `service`;
- `environment`;
- `job_name`;
- `step_name`;
- `status`;
- `warehouse_id`;
- `file_type`.

Высококардинальные значения вроде `job_id` и `file_id` не стоит добавлять во все Prometheus labels. Их лучше хранить в логах и traces. В метрики можно добавлять только тогда, когда cardinality контролируема или используется отдельная интеграция exemplars/tracing.

### Java/WildFly Monolith

Монолит должен публиковать:

- HTTP latency и 5xx rate по ERP API;
- количество загруженных файлов;
- ошибки загрузки в GCS;
- размер очереди или количество активных batch requests;
- JVM и метрики connection pool.

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

### Инфраструктура Kubernetes

Kubernetes-метрики собираются через:

- kube-state-metrics: состояние deployments, pods, jobs, cronjobs, restarts;
- node-exporter: CPU, memory, disk, network nodes;
- cAdvisor/kubelet: container CPU/memory/restarts/filesystem.

Эти метрики нужны для диагностики OOMKilled, CrashLoopBackOff, throttling, насыщения node resources и проблем autoscaling.

## Сбор метрик Prometheus

Prometheus собирает targets:

- `batch-processing-service:8080/actuator/prometheus`;
- `monolith:8080/metrics` или `/actuator/prometheus`;
- `postgres-exporter:9187/metrics`;
- Kubernetes endpoints через service discovery.

В production Kubernetes лучше использовать Prometheus Operator и `ServiceMonitor`, но для проектного задания достаточно показать scrape-конфигурацию в [prometheus/prometheus.yml](prometheus/prometheus.yml).

## Дашборды Grafana

Grafana строит несколько групп дашбордов:

### Дашборд Executive / SLA

- количество загруженных файлов за час/день;
- доля успешных и неуспешных batch jobs;
- p95/p99 длительность обработки;
- SLA violations;
- обработанные строки / строки с ошибками;
- top warehouses by failures.

### Дашборд batch operations

- активные jobs;
- длительность job по статусу;
- счётчики step read/write/skip;
- частота retry;
- failed jobs по коду ошибки;
- queue depth или pending uploads;
- throughput rows/sec.

### Дашборд приложения

- ERP HTTP latency;
- 5xx rate;
- JVM heap/non-heap;
- GC pauses;
- активные DB connections;
- thread pool utilization.

### Дашборд PostgreSQL

- `postgres_up`;
- active connections;
- slow queries;
- locks;
- transaction throughput;
- CPU/memory/disk saturation;
- deadlocks and conflicts.

### Дашборд Kubernetes

- pod restarts;
- pod readiness;
- CPU/memory requests vs usage;
- container OOMKilled;
- node pressure;
- job pod lifecycle.

## Alertmanager

Prometheus вычисляет alert rules и отправляет firing alerts в Alertmanager. Alertmanager:

- группирует связанные alerts по `service`, `severity`, `environment`;
- дедуплицирует повторяющиеся события;
- применяет inhibition, например подавляет service-level alerts, когда PostgreSQL недоступен;
- маршрутизирует notifications в Slack/Teams/email/PagerDuty;
- отправляет critical alerts дежурной SRE/platform team;
- отправляет warning alerts application support или data operations.

Пример маршрутизации:

- `severity=critical` -> on-call channel + paging;
- `severity=warning` -> team chat + ticket;
- batch data quality alerts -> data operations channel;
- infrastructure alerts -> platform/SRE channel.

## Архитектура логирования

Приложения пишут структурированные JSON-логи в stdout/stderr. Kubernetes container runtime хранит логи на nodes. Fluent Bit/Filebeat работает как DaemonSet и:

1. читает container log files;
2. обогащает записи Kubernetes metadata: namespace, pod, container, labels;
3. парсит JSON payload;
4. отправляет logs в Elasticsearch/OpenSearch.

Kibana/OpenSearch Dashboards используется для:

- поиска по `job_id`, `file_id`, `warehouse_id`, `trace_id`;
- фильтрации failed jobs по `error_code`;
- dashboards по error trends;
- support investigations и incident reviews.

## Корреляция: job_id, file_id, trace_id

Каждая загрузка должна создавать стабильные идентификаторы:

- `file_id` - уникальный идентификатор загруженного файла;
- `job_id` - Spring Batch job execution id или доменный job id;
- `warehouse_id` - складской/бизнес-контекст;
- `trace_id` - distributed trace id для request/job creation flow;
- `span_id` - current operation span id.

Рекомендуемый поток:

1. Angular отправляет upload request.
2. Monolith создаёт `file_id` и сохраняет upload metadata.
3. Monolith сохраняет CSV в GCS.
4. Monolith создаёт batch job и передаёт `file_id`, `warehouse_id`, `trace_id`.
5. Spring Batch сохраняет `job_id` и использует MDC/log context для всех logs.
6. Logs содержат `job_id`, `file_id`, `warehouse_id`, `trace_id`.
7. Metrics содержат low-cardinality labels и связываются с logs через dashboard variables или exemplars, если это поддерживается.

Это даёт операторам быстрый путь:

```text
Alert -> Grafana panel -> failing service/job -> Kibana query by job_id/file_id/trace_id -> root cause
```

## Операционный результат

Предложенный stack даёт TradeWare:

- visibility по batch SLA и throughput;
- раннее обнаружение failed jobs и DB pressure;
- централизованные structured logs вместо разрозненных файлов;
- correlation между monolith, batch service, PostgreSQL и GCS;
- observability-базу, подходящую для миграции к микросервисам и Kubernetes/cloud infrastructure.
