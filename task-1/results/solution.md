# Обоснование выбора Apache Airflow

## Почему Airflow подходит для задачи

Apache Airflow выбран как основное решение для пакетной обработки, потому что задача маркетингового отдела является типичным orchestration use case:

- нужно объединять данные из разных источников;
- запуск идет пачками, примерно до 1 млн записей за один прогон;
- важны retries, fallback, условные ветки и наблюдаемость;
- нужен понятный UI для мониторинга запусков;
- требуется расширяемость под облачные DWH, Kafka, Spark и внешние API.

Airflow не заменяет вычислительный движок для больших трансформаций, но хорошо управляет пайплайном: запускает задачи, отслеживает зависимости, повторяет упавшие шаги, отправляет уведомления и передает работу специализированным системам.

## Интеграции

### PostgreSQL

Airflow поддерживает PostgreSQL через provider `apache-airflow-providers-postgres`. В POC PostgreSQL используется в двух ролях:

- metadata database Airflow;
- demo database с таблицами `orders`, `payments`, `users`.

В реальном проекте такой подход позволяет читать операционные данные батчами, выгружать срезы в staging-слой и дальше отправлять агрегаты в DWH.

### BigQuery

Для BigQuery используется provider `apache-airflow-providers-google`. Он дает операторы и hooks для запуска SQL-запросов, загрузки файлов из GCS, экспорта результатов и работы с сервисными аккаунтами.

Production-паттерн: Airflow выгружает CSV/Parquet в GCS, запускает BigQuery load job, затем выполняет SQL-агрегацию для маркетинговых витрин.

### Redshift

Для Redshift используются Amazon provider-пакеты, например `apache-airflow-providers-amazon`. Airflow может запускать SQL в Redshift, выполнять `COPY` из S3 и оркестрировать staging -> mart pipeline.

Это подходит для сценария, где маркетинговая аналитика живет в AWS и принимает данные из S3, Kafka или PostgreSQL.

### Kafka

Kafka-интеграции доступны через provider `apache-airflow-providers-apache-kafka` и через sensor/operator-паттерны. В рамках этой задачи Kafka не реализуется кодом, чтобы не усложнять локальный POC.

В production Kafka можно использовать так:

- события модификации заказов складываются в Kafka topics;
- Airflow запускает batch job по расписанию или событию;
- job читает compacted topic или подготовленный landing-слой;
- данные объединяются с PostgreSQL и CSV/DWH-источниками.

Для event-driven сценариев можно использовать Airflow Datasets, deferrable sensors или внешний trigger через Airflow REST API.

### Spark

Для Spark есть provider `apache-airflow-providers-apache-spark`. Airflow может запускать Spark jobs через `SparkSubmitOperator`, Kubernetes Spark Operator, Dataproc, EMR или другой managed Spark сервис.

Это важно для роста объема: если 1 млн записей превращается в десятки или сотни миллионов, Airflow остается orchestrator, а тяжелые трансформации выносятся в Spark.

### Внешние API

Airflow хорошо подходит для интеграции с HTTP API:

- `HttpHook` и HTTP operators;
- кастомные Python-задачи;
- retries, timeouts, exponential backoff;
- сохранение ответов в object storage или DWH.

Для маркетинга это полезно при загрузке данных из рекламных кабинетов, CRM, CDP и email-платформ.

## Provider-пакеты

Сильная сторона Airflow - ecosystem provider-пакетов. Они отделяют ядро Airflow от интеграций:

- `apache-airflow-providers-postgres`;
- `apache-airflow-providers-google`;
- `apache-airflow-providers-amazon`;
- `apache-airflow-providers-apache-kafka`;
- `apache-airflow-providers-apache-spark`;
- `apache-airflow-providers-http`;
- `apache-airflow-providers-cncf-kubernetes`.

Это снижает стоимость развития: новые источники и назначения подключаются через готовые hooks, operators и sensors, а не через полностью самописный orchestration layer.

## DAG, ветвление, условия и событийные триггеры

Airflow описывает pipeline как DAG: задачи, зависимости и правила запуска явно видны в коде и UI.

Для этой задачи важны:

- `BranchPythonOperator` - выбор ветки обработки по объему данных;
- condition operators и trigger rules - управление ветками и downstream-поведением;
- sensors и deferrable operators - ожидание файлов, событий и внешних состояний;
- Airflow Datasets - запуск DAG при обновлении набора данных;
- REST API - внешний trigger, например после загрузки файла или завершения upstream-системы.

В POC ветвление реализовано так: если суммарное число записей из PostgreSQL и CSV больше порога, запускается `high_volume_processing`; иначе запускается `normal_processing`.

## Retry, fallback и email-уведомления

Для batch-процессов важны операционные гарантии:

- `retries=3` и `retry_delay` на задачах;
- `email_on_failure` и `email_on_retry` в default args;
- отдельные notification tasks через `EmailOperator`;
- fallback-ветки через branch/trigger rules;
- понятные логи с бизнес-результатом.

В production fallback может быть расширен:

- если BigQuery недоступен, положить результат в object storage;
- если API отвечает ошибкой, использовать последнюю успешную выгрузку;
- если high-volume job не прошел, отправить алерт и переключить downstream на предыдущую витрину.

## Мониторинг

Airflow дает базовую наблюдаемость из коробки:

- UI со статусами DAG/task runs;
- история retry;
- логи задач;
- SLA/alerts;
- email-уведомления;
- metrics через StatsD/Prometheus/Grafana при production-настройке.

Для production рекомендуется добавить централизованные логи, метрики длительности задач и объема данных, алерты по failed DAG runs, data quality checks после загрузки и lineage/каталог данных при необходимости.

## Развертывание в облаке

### Kubernetes

Airflow можно развернуть в Kubernetes через Helm chart. Это дает горизонтальное масштабирование workers, KubernetesExecutor или CeleryExecutor, изоляцию задач в pod'ах, интеграцию с secrets/config maps и удобный путь к Spark-on-Kubernetes.

### Astronomer

Astronomer - managed/commercial платформа вокруг Airflow. Подходит, если нужна быстрая эксплуатация Airflow без самостоятельной сборки платформы, observability, governance и удобный CI/CD для DAG.

### Google Cloud Composer

Cloud Composer - managed Airflow в Google Cloud. Хороший выбор, если целевая аналитическая платформа - BigQuery/GCS: есть нативная интеграция с Google Cloud IAM, GCS, BigQuery и Dataproc.

### Amazon MWAA

Amazon Managed Workflows for Apache Airflow подходит для AWS-ландшафта: интеграция с S3, Redshift, Glue, EMR, IAM-based security и managed Airflow environment.

## Итог

Apache Airflow закрывает ключевые требования задачи: гибкий batch pipeline, ветвление, retries, fallback-логика, email-уведомления, мониторинг и богатый набор интеграций. Локальный POC демонстрирует основной orchestration-подход на PostgreSQL и CSV, а production-архитектура может быть расширена Kafka/Spark/DWH-интеграциями без смены инструмента оркестрации.
