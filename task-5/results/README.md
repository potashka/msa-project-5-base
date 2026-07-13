# Задача 5. Архитектура наблюдаемости для TradeWare

В этой папке находятся проектные материалы по мониторингу, логированию и оповещениям для архитектуры TradeWare с Java/WildFly, Spring Batch, PostgreSQL, GCS и Kubernetes/cloud-инфраструктурой.

Это не готовый к промышленной эксплуатации Helm-стек. Результат задания: архитектура наблюдаемости, каталог метрик, формат логов, правила алертов, C4-диаграмма и примеры конфигураций.

## Файлы результата

- [monitoring-logging-solution.md](monitoring-logging-solution.md) - общая архитектура Prometheus, Grafana, Alertmanager, Micrometer, PostgreSQL Exporter, экспортеров Kubernetes и логирования через ELK/OpenSearch.
- [metrics.md](metrics.md) - каталог технических, бизнес и SLA-метрик с примерами условий для алертов.
- [logging.md](logging.md) - формат структурированных JSON-логов, обязательные поля и события INFO/WARN/ERROR.
- [alerting-rules.md](alerting-rules.md) - описание ключевых алертов и уровней критичности.
- [c4-observability-to-be.puml](c4-observability-to-be.puml) - целевая C4-диаграмма потоков метрик, логов и алертов.
- [prometheus/prometheus.yml](prometheus/prometheus.yml) - пример конфигурации сбора метрик Prometheus.
- [prometheus/alert-rules.yml](prometheus/alert-rules.yml) - пример правил алертов Prometheus.
- [elk/fluent-bit.conf](elk/fluent-bit.conf) - пример конфигурации Fluent Bit для отправки контейнерных логов в Elasticsearch/OpenSearch.
- [README.md](README.md) - описание состава результата и скриншотов.

## Выбранный стек

- Prometheus + Grafana + Alertmanager для метрик и алертинга.
- Micrometer + Spring Boot Actuator для метрик сервиса Spring Batch.
- PostgreSQL Exporter для метрик базы данных.
- kube-state-metrics / node-exporter / cAdvisor для Kubernetes-инфраструктуры.
- Fluent Bit или Filebeat для логов.
- Elasticsearch или OpenSearch + Kibana/OpenSearch Dashboards для централизованного логирования.

## Как экспортировать C4-диаграмму

Из директории `task-5/results`:

```bash
plantuml -tpng c4-observability-to-be.puml
```

Вариант с Docker:

```bash
docker run --rm -v "$PWD:/work" plantuml/plantuml -tpng /work/c4-observability-to-be.puml
```

PowerShell:

```powershell
docker run --rm -v "${PWD}:/work" plantuml/plantuml -tpng /work/c4-observability-to-be.puml
```

Диаграмма использует C4-PlantUML из GitHub. Если PlantUML запускается без доступа в интернет, скачайте библиотеку C4-PlantUML локально и замените URL в `!include` внутри `.puml` файла.

## Скриншоты и диаграммы для сдачи

Рекомендуемые артефакты:

1. `c4_observability_to_be.png` - отрендеренная C4-диаграмма наблюдаемости.
2. `metrics_catalog.png` - ключевая часть `metrics.md` с метриками пакетной обработки, SLA, JVM, БД и Kubernetes.
3. `logging_format.png` - JSON-формат логов из `logging.md`.
4. `alerting_rules.png` - таблица алертов из `alerting-rules.md`.
5. `prometheus_config.png` - пример конфигурации сбора метрик.
6. `fluent_bit_config.png` - пример конфигурации доставки логов.

## Примечания

Для реального промышленного развёртывания следующим шагом нужно упаковать решение в Helm/Kustomize и добавить:

- ресурсы `ServiceMonitor` для Prometheus Operator;
- дашборды Grafana в формате JSON;
- маршруты и получателей Alertmanager;
- шаблоны индексов OpenSearch и политики жизненного цикла;
- инструкции реагирования, связанные с аннотациями алертов.
