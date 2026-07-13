# Задача 1. POC пакетной обработки на Apache Airflow

Решение демонстрирует пакетную обработку маркетинговых данных в Apache Airflow:

- чтение заказов, платежей и пользователей из PostgreSQL;
- чтение статусов доставок из CSV;
- простая аналитика по заказам, выручке и доставкам;
- ветвление через `BranchPythonOperator`;
- повторные попытки для задач;
- email-уведомления об успехе и ошибке через локальный SMTP MailHog.

POC намеренно не содержит Spark/Kafka-код: локальная демонстрация сфокусирована на простом пайплайне пакетной обработки. Интеграции с Kafka, Spark, BigQuery и Redshift описаны в [solution.md](solution.md).

## Структура

```text
task-1/results/
  dags/tradeware_marketing_batch_dag.py
  data/deliveries.csv
  sql/init.sql
  screenshots/
  docker-compose.yml
  README.md
  solution.md
```

## Требования для Windows 11

1. Установить WSL2.
2. Установить Docker Desktop.
3. В Docker Desktop включить интеграцию с WSL2: `Settings -> Resources -> WSL Integration`.
4. Открыть проект из WSL2 или из PowerShell в корне репозитория.

Проверка:

```powershell
docker --version
docker compose version
```

## Локальный запуск

Перейти в каталог решения:

```powershell
cd task-1\results
```

Запустить стек:

```powershell
docker compose up airflow-init
docker compose up -d
```

Первый запуск может занять несколько минут: контейнеры Airflow установят provider-пакет PostgreSQL и Python-зависимость `psycopg2-binary`.

Открыть сервисы:

- Airflow UI: http://localhost:8080
- MailHog UI: http://localhost:8025

Доступ в Airflow:

- логин: `airflow`
- пароль: `airflow`

## Запуск DAG

1. Открыть Airflow UI.
2. Найти DAG `tradeware_marketing_batch_dag`.
3. Включить DAG тумблером.
4. Нажать `Trigger DAG`.
5. Открыть `Grid` или `Graph` и дождаться завершения.
6. Открыть логи задач `combine_and_analyze`, `normal_processing` или `high_volume_processing`.

В логах будет результат вроде:

```text
Marketing batch summary: orders=6, payments=6, users=4, deliveries=6, paid_revenue=3060.00
Delivery status breakdown: {'in_transit': 1, 'delivered': 3, 'cancelled': 1, 'delayed': 1}
```

Для демонстрации ветвления используется порог `BATCH_VOLUME_THRESHOLD=10`. В демо-данных 22 записи суммарно, поэтому DAG пойдет в ветку `high_volume_processing`. Порог можно поменять в `docker-compose.yml`.

## Email-уведомления

Airflow настроен на локальный SMTP MailHog:

- SMTP host: `mailhog`
- SMTP port: `1025`
- веб-интерфейс писем: http://localhost:8025

После успешного запуска DAG в MailHog появится письмо от задачи `send_success_email`. При ошибке любой ключевой вышестоящей задачи сработает `send_failure_email`.

## Остановка

```powershell
docker compose down
```

Полная очистка контейнеров и томов:

```powershell
docker compose down -v
```

## Скриншоты для сдачи

Папка `screenshots/` добавлена специально для артефактов сдачи. Рекомендуется сохранить туда:

1. `airflow_dag_list.png` - DAG `tradeware_marketing_batch_dag` виден в Airflow UI.
2. `airflow_graph_success.png` - представление Graph/Grid с успешным запуском и выбранной веткой.
3. `airflow_task_logs.png` - логи `combine_and_analyze` с итоговой аналитикой.
4. `mailhog_success_email.png` - письмо об успешном завершении в MailHog.
5. `docker_compose_ps.png` - вывод `docker compose ps` с запущенными сервисами.
