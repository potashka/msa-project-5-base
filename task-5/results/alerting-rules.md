# Правила алертинга

## Модель критичности

- `warning`: сервис деградировал или близок к порогу SLA/риска. Нужна реакция человека в рабочее время или со стороны команды поддержки.
- `critical`: есть пользовательская ошибка, обработка данных остановлена или зависимость недоступна. Требуется реакция дежурного.

## Алерты

| Алерт | Критичность | Условие | Почему важно | Рекомендуемое действие |
|---|---|---|---|---|
| Ошибка job | critical | `increase(batch_job_failed_total[5m]) > 0` | CSV-отчёт не обработался, nomenclature может устареть. | Открыть логи по `job_id`, проверить код ошибки, повторить запуск, если это безопасно. |
| Длительность job выше SLA | warning / critical | p95 `batch_job_duration_seconds` > 30s для jobs на 2 000 строк в течение 10m; critical, если > 60s. | Бизнес-цель - обработка 2 000 строк за 30 секунд. | Проверить DB latency, retry count, GCS latency, CPU/memory pod. |
| Слишком много пропущенных строк | warning | `batch_step_skip_count / batch_step_read_count > 0.01` за 10m | Проблема качества данных может повлиять на складские отчёты. | Проверить error report, уведомить владельца данных, проверить изменения формата файла. |
| Нет успешных jobs за N часов | critical | нет прироста `batch_job_success_total` за 2h в ожидаемом окне нагрузки | Пайплайн может быть зависшим, даже если нет отдельной failed job. | Проверить pending jobs, scheduler/queue и health batch service. |
| PostgreSQL недоступен | critical | `postgres_up == 0` в течение 1m | Batch и ERP persistence затронуты. | Эскалировать DBA/platform, проверить DB pod/managed service/network. |
| Высокое число DB connections | warning / critical | active pool connections > 80% за 10m; > 95% за 5m как critical | Batch jobs могут вытеснить ERP online traffic. | Снизить batch concurrency, проверить slow queries, аккуратно масштабировать DB/pool. |
| Высокое число перезапусков pod | warning / critical | pod restarts increased > 3 за 15m; critical для core services | Crash loops или OOM могут нарушить обработку. | Проверить pod events, container logs, memory limits. |
| Высокая доля 5xx | critical | 5xx rate > 5% за 5m на monolith или batch API | Пользователи не могут надёжно загружать файлы или проверять статус. | Проверить recent deploy, dependencies, exceptions. |
| Ошибки доступа к GCS | critical | `increase(gcs_request_errors_total[5m]) > 0` | Файлы нельзя сохранить/прочитать, batch processing останавливается. | Проверить credentials, IAM, bucket availability, object paths. |
| Высокая частота retry | warning | `increase(batch_retry_total[10m]) > threshold` | Нестабильность временных зависимостей растёт. | Проверить DB/GCS latency и network errors. |
| Большой backlog batch jobs | warning / critical | pending jobs > threshold или oldest pending job > 15m | SLA под риском, даже если jobs в итоге завершатся. | Масштабировать workers или уменьшить concurrency bottlenecks. |
| Высокое потребление JVM memory | warning | heap usage > 85% за 15m | Риск GC pauses или OOMKilled. | Проверить memory dashboard, при необходимости снять heap dump, настроить limits. |
| Давление на Kubernetes node | warning | node memory/disk pressure active | Pods могут быть evicted, jobs могут прерываться. | Добавить capacity или перенести workloads. |

## Маршрутизация алертов

- `severity=critical`, `service=spring-batch-processing-service` -> SRE on-call + batch support channel.
- `severity=critical`, `service=postgresql` -> SRE on-call + DBA.
- `severity=warning`, `type=data_quality` -> data operations team.
- `severity=warning`, `type=capacity` -> platform team.

## Правила снижения шума

- Группировать job failure alerts по `environment`, `service`, `job_name`, `warehouse_id`.
- Не отправлять page на каждую skipped row; алертить по агрегированному skip ratio.
- Подавлять downstream service-level alerts, когда `postgres_up == 0`.
- Добавить runbooks в annotations каждого critical alert.
- Использовать маршрутизацию в business hours для warning data-quality alerts, если SLA не требует реакции 24/7.
