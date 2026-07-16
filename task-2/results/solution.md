# Решение: Kubernetes CronJob для экспорта B2B-прайс-листов

## Выбранный подход

Для TradeWare выбирается решение на базе **Kubernetes CronJob**. Каждый день в 06:00 Kubernetes запускает контейнер `price-list-exporter`, который читает актуальные данные из PostgreSQL, формирует кастомные прайс-листы для B2B-клиентов и сохраняет результат в файловое хранилище.

Это дизайн-решение для задачи 2. Полноценный код exporter-приложения не реализуется здесь и будет относиться к задаче 3.

## Поток выполнения

1. Kubernetes CronJob с расписанием `0 6 * * *` создает Job и Pod.
2. Pod запускает контейнер `price-list-exporter`.
3. Приложение получает параметры подключения к PostgreSQL:
   - host, port, database и нечувствительные настройки из `ConfigMap`;
   - username, password и другие секреты из `Secret`.
4. Exporter выполняет SQL-запрос с JOIN по таблицам:
   - `products`;
   - `categories`;
   - `clients`;
   - `client_prices`.
5. Для каждого B2B-клиента или группы клиентов формируется CSV или XLS-файл с актуальными ценами.
6. Результат сохраняется:
   - в production: в object storage, например GCS или S3;
   - в локальном POC: в PVC, смонтированный в Pod.
7. Приложение пишет структурные логи в stdout/stderr.
8. Kubernetes фиксирует статус Job: `Succeeded` или `Failed`.
9. Prometheus и централизованное логирование собирают метрики, события и логи.

## Основные компоненты

### Kubernetes CronJob

CronJob отвечает только за расписание и жизненный цикл batch-запуска:

- `schedule: "0 6 * * *"`;
- `timeZone: "Europe/Moscow"`, если кластер поддерживает это поле и бизнес-время должно быть зафиксировано явно;
- `concurrencyPolicy: Forbid`, чтобы не запускать второй экспорт, если предыдущий еще не завершился;
- `backoffLimit`, чтобы ограничить количество повторов при ошибке;
- `successfulJobsHistoryLimit` и `failedJobsHistoryLimit`, чтобы хранить разумную историю запусков;
- resource requests/limits, чтобы batch-процесс не вытеснял runtime микросервисы.

### price-list-exporter

`price-list-exporter` - небольшой stateless-контейнер. Он не хранит состояние между запусками и может быть пересобран/перезапущен без миграции данных.

Обязанности контейнера:

- подключиться к PostgreSQL;
- выполнить подготовленный SQL JOIN;
- сформировать CSV или XLS;
- сохранить файл в выбранное хранилище;
- записать структурные логи о старте, количестве обработанных клиентов/строк, имени файла, длительности и результате выполнения;
- завершиться с exit code `0` при успехе или non-zero при ошибке.

### PostgreSQL

PostgreSQL остаётся source of truth для прайс-листов. Для стабильности утреннего экспорта рекомендуется:

- использовать read-only пользователя;
- читать данные в транзакции с консистентным snapshot, если важна строгая согласованность;
- добавить индексы по foreign key и полям фильтрации, если они отсутствуют;
- не выполнять тяжелую бизнес-логику в exporter, если ее можно выразить SQL-запросом.

### File/Object Storage

Production-вариант:

- S3, GCS или совместимое object storage;
- путь вида `price-lists/yyyy-mm-dd/client-id.csv`;
- bucket lifecycle policy для хранения истории;
- IAM/ServiceAccount вместо статических ключей, если это поддерживается облаком.

Локальный POC-вариант:

- PVC, смонтированный в `/exports`;
- файл вида `/exports/price-lists-2026-07-07.csv`.

### Логирование и мониторинг

Exporter пишет структурные JSON-логи, например:

```json
{"event":"price_list_export_started","schedule":"0 6 * * *"}
{"event":"price_list_export_finished","clients":320,"rows":18500,"duration_ms":4200,"status":"success"}
```

Наблюдаемость обеспечивается стандартным Kubernetes/cloud-native стеком:

- `kubectl get jobs` и `kubectl describe job` для статуса;
- `kubectl logs job/<job-name>` для логов запуска;
- Prometheus/Grafana для метрик Job, Pod и контейнера;
- Loki/ELK/Cloud Logging для централизованных логов;
- алертинг по failed Job, превышению длительности выполнения и отсутствию успешного запуска после 06:00.

## Почему это решение подходит

Kubernetes CronJob даёт ровно нужный уровень orchestration для маленькой регулярной batch-задачи. Он не требует отдельной платформы наподобие Airflow, не вводит распределённый compute наподобие Spark и хорошо ложится в существующую микросервисную инфраструктуру TradeWare.
