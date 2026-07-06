# Alternatives for TradeWare ETL

## Decision context

TradeWare needs to move heavy CSV processing out of the Java/WildFly monolith. The near-term target is reliable ETL for warehouse reports:

- about 400 000 rows per day;
- 2-3x growth on peak days;
- 100-150 parallel uploads in peak hours;
- average processing time for a 2 000-row report up to 30 seconds;
- Java team, PostgreSQL and GCS are already in place;
- migration path toward microservices is required.

Spring Batch is selected for the nearest stage because it solves the current pain with the smallest technology jump.

## Comparison

| Alternative | Strengths | Weaknesses for this case | Fit |
|---|---|---|---|
| Apache Airflow | Strong orchestration, DAG UI, retries, scheduling, good visibility for multi-step pipelines. | Airflow is an orchestrator, not a row-level processing engine. For chunk processing, per-row validation, skip/retry and JDBC upsert, another worker/service is still needed. Adds a separate platform to operate. | Useful later if TradeWare needs many dependent data pipelines, scheduled workflows and cross-system orchestration. Not the best first extraction step. |
| Kubernetes CronJob | Simple cloud-native scheduled jobs, easy deployment in Kubernetes, low overhead. | The workload is user-triggered uploads with many parallel files, not only a scheduled daily task. CronJob has limited job lifecycle UX and no built-in chunk restartability, skip policy or JobRepository. | Good for simple scheduled exports/imports. Too primitive for interactive CSV upload processing at peak concurrency. |
| Apache Spark | Distributed processing, strong for large datasets, partitioning, scalable compute. | Operationally heavier. Requires Spark cluster/operator or managed service. For 400k-1.2M rows/day and 2k-row reports, Spark is likely overkill. Java team would face a bigger implementation and operations shift. | Good if data grows to tens/hundreds of millions of rows or transformations become analytical and distributed. |
| Google Dataflow / Apache Beam | Managed scaling, strong batch/stream model, GCP-native, good for large data pipelines. | Requires Beam programming model and stronger cloud coupling. More expensive learning curve and operational model change than Spring Batch. Integration with monolith status UX and row-level business validation needs extra design. | Strong future option for cloud-native data platform migration. Not the smallest near-term step. |
| Kafka Streams | Excellent for event streams, stateful stream processing, continuous updates. | Current source is uploaded CSV files in GCS. Kafka Streams is not a natural fit for file-based import with chunk restartability and skip reports. Would require converting file rows into events and designing topics, ordering and replay. | Useful later if TradeWare moves to event-driven inventory/nomenclature updates. Not ideal for CSV ETL extraction from monolith. |
| Spring Batch | Built for batch jobs, chunk-oriented processing, retry/skip/restartability, JobRepository, Java/JDBC integration, familiar to Java teams. | Adds a new service and metadata repository. Needs careful idempotency, parallelism control and DB load management. Not a distributed big-data engine. | Best near-term choice for extracting CSV processing from Java monolith while staying close to the existing stack. |

## Why Spring Batch is selected for the nearest stage

Spring Batch directly addresses the current failure mode: long-running row-by-row processing blocks the online monolith. It moves the workload into a dedicated processing service while preserving familiar Java, PostgreSQL and GCS integration.

Key reasons:

- chunk-oriented processing reduces transaction overhead and avoids loading whole files into memory;
- JobRepository gives job/step status, restartability and execution history;
- retry, skip and backoff policies are first-class patterns;
- idempotent upsert can be implemented close to existing domain logic;
- Java team can reuse existing validation/enrichment code more easily than with Spark/Dataflow;
- the monolith can evolve into a thin upload/status facade without a full rewrite;
- Kubernetes scaling can be added incrementally through more service replicas, partitioning and concurrency limits.

## Limitations of Spring Batch

Spring Batch is not a universal data platform. Its main limitations for TradeWare are:

- it does not remove the need to design concurrency control;
- PostgreSQL can still become the bottleneck if too many jobs write at once;
- partitioning/multithreaded steps require thread-safe readers, processors and writers;
- JobRepository must be monitored and maintained;
- very large distributed workloads may eventually need Spark or Dataflow;
- asynchronous UX must be designed explicitly in the monolith and frontend;
- operational maturity is required: dashboards, alerts, failed job handling, restart procedures and runbooks.

## Recommended evolution

1. Extract CSV processing into Spring Batch Processing Service.
2. Add JobRepository, status API and async upload UX.
3. Add metrics, logs, alerting and operational runbooks.
4. Tune chunk size, DB indexes, batch writes and connection pools.
5. Add controlled parallelism and partitioning after baseline measurements.
6. Revisit Airflow/Dataflow/Spark only if pipelines become cross-system, strongly scheduled or truly distributed at larger scale.
