# Структурированное логирование

## Формат логов

Все сервисы TradeWare должны писать структурированные JSON-логи в stdout/stderr. Fluent Bit/Filebeat собирает контейнерные логи и отправляет их в Elasticsearch/OpenSearch.

Обязательные поля:

```json
{
  "timestamp": "2026-07-07T20:00:01.123Z",
  "level": "INFO",
  "service": "spring-batch-processing-service",
  "environment": "prod",
  "job_id": "job-84219",
  "file_id": "file-20260707-00042",
  "warehouse_id": "wh-17",
  "step_name": "validate-and-enrich",
  "trace_id": "4f3c2a4d7a1b4e2f9c0a123456789abc",
  "span_id": "9f0a1b2c3d4e5f60",
  "error_code": null,
  "message": "Batch step finished"
}
```

Дополнительные рекомендуемые поля:

- `duration_ms`;
- `rows_read`;
- `rows_written`;
- `rows_skipped`;
- `retry_count`;
- `file_uri`;
- `http_method`;
- `http_path`;
- `status_code`;
- `exception_class`;
- `stacktrace`;
- `pod_name`;
- `namespace`.

Метаданные Kubernetes могут добавляться через Fluent Bit/Filebeat, поэтому приложениям не нужно вручную логировать labels pod/node.

## Обязательные поля

| Поле | Описание |
|---|---|
| `timestamp` | Время события в формате ISO-8601 UTC. |
| `level` | `INFO`, `WARN`, `ERROR`. |
| `service` | Имя сервиса: monolith, batch service, side logs postgres-exporter и т.д. |
| `environment` | `dev`, `stage`, `prod`. |
| `job_id` | Идентификатор batch job. Может быть null для логов вне batch-процессов. |
| `file_id` | Идентификатор загруженного CSV-файла. |
| `warehouse_id` | Бизнес-контекст загрузки или отчёта. |
| `step_name` | Имя Spring Batch step. Может быть null вне batch steps. |
| `trace_id` | Distributed trace id, передаваемый от запроса загрузки к batch job. |
| `span_id` | Идентификатор текущей операции span. |
| `error_code` | Стабильный код ошибки приложения, например `CSV_VALIDATION_FAILED`. |
| `message` | Человекочитаемое сообщение. |

## Уровни логирования

### INFO

Использовать `INFO` для ожидаемых событий жизненного цикла:

- CSV-загрузка принята монолитом;
- файл сохранён в GCS;
- batch job создана;
- batch job запущена;
- step запущен;
- checkpoints прогресса chunk, если это не создаёт слишком много шума;
- step завершён со счётчиками;
- job успешно завершена;
- статус запрошен через UI.

Пример:

```json
{
  "timestamp": "2026-07-07T20:02:31.001Z",
  "level": "INFO",
  "service": "spring-batch-processing-service",
  "environment": "prod",
  "job_id": "job-84219",
  "file_id": "file-20260707-00042",
  "warehouse_id": "wh-17",
  "step_name": "write-nomenclature",
  "trace_id": "4f3c2a4d7a1b4e2f9c0a123456789abc",
  "span_id": "1133557799aabbcc",
  "error_code": null,
  "message": "Batch job completed successfully",
  "rows_read": 2000,
  "rows_written": 1996,
  "rows_skipped": 4,
  "duration_ms": 24820
}
```

### WARN

Использовать `WARN` для восстанавливаемых или бизнес-значимых проблем:

- строка пропущена из-за ошибки валидации;
- retry успешно завершился после временной ошибки DB/GCS;
- длительность обработки близка к SLA threshold;
- skip count превысил warning threshold;
- GCS upload медленный, но успешный;
- глубина batch queue высока, но ещё в пределах лимитов.

Не стоит логировать каждую пропущенную строку на уровне `WARN`, если файлы могут содержать много невалидных строк. Лучше писать агрегированное предупреждение и error report в GCS.

### ERROR

Использовать `ERROR` для неуспешных операций, требующих расследования:

- job завершилась ошибкой;
- step завершился ошибкой;
- доступ к GCS запрещён;
- PostgreSQL недоступен;
- запись в БД не удалась после retries;
- непредвиденное исключение;
- обновление статуса не удалось;
- monolith failed to create batch job.

Каждый `ERROR` log должен включать:

- `error_code`;
- `exception_class`;
- `stacktrace`;
- `job_id` и `file_id`, если доступны;
- достаточно контекста, чтобы воспроизвести проблему или найти неуспешный input.

## Стратегия корреляции

Использовать MDC/log context в Java-сервисах:

- monolith задаёт `trace_id`, `file_id`, `warehouse_id`;
- batch service задаёт `job_id`, `step_name`, `file_id`, `warehouse_id`;
- эти поля автоматически добавляются в каждую строку лога в контексте выполнения.

Типовые запросы Kibana/OpenSearch:

```text
job_id:"job-84219"
file_id:"file-20260707-00042"
warehouse_id:"wh-17" AND level:"ERROR"
trace_id:"4f3c2a4d7a1b4e2f9c0a123456789abc"
error_code:"GCS_ACCESS_DENIED"
```

## Хранение

Рекомендуемый срок хранения:

- application logs: 14-30 дней в hot storage;
- error logs и audit logs: 90 дней или согласно compliance;
- большие stacktraces и debug logs: более короткий retention;
- GCS error reports: в соответствии с требованиями бизнес-аудита.
