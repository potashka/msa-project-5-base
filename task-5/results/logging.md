# Structured logging

## Log format

All TradeWare services should write structured JSON logs to stdout/stderr. Fluent Bit/Filebeat collects container logs and sends them to Elasticsearch/OpenSearch.

Required fields:

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

Additional recommended fields:

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

Kubernetes metadata can be added by Fluent Bit/Filebeat, so applications do not need to manually log pod/node labels.

## Required fields

| Field | Description |
|---|---|
| `timestamp` | Event time in ISO-8601 UTC format. |
| `level` | `INFO`, `WARN`, `ERROR`. |
| `service` | Service name: monolith, batch service, postgres-exporter side logs, etc. |
| `environment` | `dev`, `stage`, `prod`. |
| `job_id` | Batch job identifier. Nullable for non-batch logs. |
| `file_id` | Uploaded CSV file identifier. |
| `warehouse_id` | Business context of the upload/report. |
| `step_name` | Spring Batch step name. Nullable outside batch steps. |
| `trace_id` | Distributed trace id propagated from upload request to batch job. |
| `span_id` | Current operation span id. |
| `error_code` | Stable application error code, for example `CSV_VALIDATION_FAILED`. |
| `message` | Human-readable message. |

## Log levels

### INFO

Use `INFO` for expected lifecycle events:

- CSV upload accepted by monolith;
- file saved to GCS;
- batch job created;
- batch job started;
- step started;
- chunk progress checkpoints, if not too noisy;
- step completed with counters;
- job completed successfully;
- status requested by UI.

Example:

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

Use `WARN` for recoverable or business-significant issues:

- row skipped due to validation error;
- retry succeeded after transient DB/GCS failure;
- processing duration is near SLA threshold;
- skip count exceeds warning threshold;
- GCS upload is slow but successful;
- batch queue depth is high but still within limits.

Avoid logging every skipped row at `WARN` if files can contain many invalid rows. Prefer aggregated warning plus error report in GCS.

### ERROR

Use `ERROR` for failed operations requiring investigation:

- job failed;
- step failed;
- GCS access denied;
- PostgreSQL unavailable;
- DB write failed after retries;
- unexpected exception;
- status update failed;
- monolith failed to create batch job.

Every `ERROR` log should include:

- `error_code`;
- `exception_class`;
- `stacktrace`;
- `job_id` and `file_id` when available;
- enough context to reproduce or find the failed input.

## Correlation strategy

Use MDC/log context in Java services:

- monolith sets `trace_id`, `file_id`, `warehouse_id`;
- batch service sets `job_id`, `step_name`, `file_id`, `warehouse_id`;
- these fields are automatically appended to every log line in the execution context.

Kibana/OpenSearch common queries:

```text
job_id:"job-84219"
file_id:"file-20260707-00042"
warehouse_id:"wh-17" AND level:"ERROR"
trace_id:"4f3c2a4d7a1b4e2f9c0a123456789abc"
error_code:"GCS_ACCESS_DENIED"
```

## Retention

Suggested retention:

- application logs: 14-30 days hot storage;
- error logs and audit logs: 90 days or according to compliance;
- large stacktraces and debug logs: shorter retention;
- GCS error reports: aligned with business audit requirements.
