# Task 5. Observability architecture for TradeWare

В этой папке находятся проектные материалы по мониторингу, логированию и оповещениям для архитектуры TradeWare с Java/WildFly, Spring Batch, PostgreSQL, GCS и Kubernetes/cloud infrastructure.

Это не production-ready Helm stack. Результат задания: архитектура observability, каталог метрик, формат логов, правила алертов, C4-диаграмма и примеры конфигураций.

## Result files

- [monitoring-logging-solution.md](monitoring-logging-solution.md) - общая архитектура Prometheus, Grafana, Alertmanager, Micrometer, PostgreSQL Exporter, Kubernetes exporters и ELK/OpenSearch logging.
- [metrics.md](metrics.md) - каталог технических, бизнес и SLA-метрик с примерами alert conditions.
- [logging.md](logging.md) - формат структурированных JSON-логов, обязательные поля и события INFO/WARN/ERROR.
- [alerting-rules.md](alerting-rules.md) - описание ключевых алертов и severity.
- [c4-observability-to-be.puml](c4-observability-to-be.puml) - C4 To Be диаграмма потоков метрик, логов и алертов.
- [prometheus/prometheus.yml](prometheus/prometheus.yml) - пример scrape-конфига Prometheus.
- [prometheus/alert-rules.yml](prometheus/alert-rules.yml) - пример Prometheus alert rules.
- [elk/fluent-bit.conf](elk/fluent-bit.conf) - пример Fluent Bit конфигурации для отправки container logs в Elasticsearch/OpenSearch.
- [README.md](README.md) - описание состава результата и скриншотов.

## Selected stack

- Prometheus + Grafana + Alertmanager for metrics and alerting.
- Micrometer + Spring Boot Actuator for Spring Batch service metrics.
- PostgreSQL Exporter for database metrics.
- kube-state-metrics / node-exporter / cAdvisor for Kubernetes infrastructure.
- Fluent Bit or Filebeat for logs.
- Elasticsearch or OpenSearch + Kibana/OpenSearch Dashboards for centralized logging.

## How to export C4 diagram

From `task-5/results`:

```bash
plantuml -tpng c4-observability-to-be.puml
```

Docker option:

```bash
docker run --rm -v "$PWD:/work" plantuml/plantuml -tpng /work/c4-observability-to-be.puml
```

PowerShell:

```powershell
docker run --rm -v "${PWD}:/work" plantuml/plantuml -tpng /work/c4-observability-to-be.puml
```

The diagram uses C4-PlantUML from GitHub. If PlantUML runs without internet access, download the C4-PlantUML library locally and replace the `!include` URL in the `.puml` file.

## Screenshots / diagrams for submission

Recommended artifacts:

1. `c4_observability_to_be.png` - rendered C4 observability diagram.
2. `metrics_catalog.png` - key part of `metrics.md` with batch, SLA, JVM, DB and Kubernetes metrics.
3. `logging_format.png` - JSON log format from `logging.md`.
4. `alerting_rules.png` - alert table from `alerting-rules.md`.
5. `prometheus_config.png` - scrape config example.
6. `fluent_bit_config.png` - log shipping config example.

## Notes

For a real production rollout, the next step would be to package this into Helm/Kustomize and add:

- Prometheus Operator `ServiceMonitor` resources;
- Grafana dashboards as JSON;
- Alertmanager routes and receivers;
- OpenSearch index templates and lifecycle policies;
- runbooks linked from alert annotations.
