from __future__ import annotations

import csv
import logging
import os
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

from airflow import DAG
from airflow.operators.email import EmailOperator
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import BranchPythonOperator, PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.utils.trigger_rule import TriggerRule


LOGGER = logging.getLogger(__name__)

DEMO_POSTGRES_CONN_ID = "demo_postgres"
DELIVERIES_PATH = Path("/opt/airflow/data/deliveries.csv")
VOLUME_THRESHOLD = int(os.getenv("BATCH_VOLUME_THRESHOLD", "10"))


default_args = {
    "owner": "tradeware-data-platform",
    "depends_on_past": False,
    "retries": 3,
    "retry_delay": timedelta(minutes=1),
    "email": ["marketing-ops@example.local"],
    "email_on_failure": True,
    "email_on_retry": False,
}


def extract_postgres_data(**context):
    """Читает демо-данные из PostgreSQL и считает базовые агрегаты."""
    hook = PostgresHook(postgres_conn_id=DEMO_POSTGRES_CONN_ID)

    orders = hook.get_records(
        """
        SELECT order_id, user_id, status, total_amount, created_at
        FROM orders
        ORDER BY order_id
        """
    )
    payments = hook.get_records(
        """
        SELECT payment_id, order_id, payment_status, amount, paid_at
        FROM payments
        ORDER BY payment_id
        """
    )
    users = hook.get_records(
        """
        SELECT user_id, email, full_name, city, created_at
        FROM users
        ORDER BY user_id
        """
    )

    paid_revenue = sum(float(row[3]) for row in payments if row[2] == "paid")
    result = {
        "orders_count": len(orders),
        "payments_count": len(payments),
        "users_count": len(users),
        "paid_revenue": paid_revenue,
    }

    LOGGER.info("PostgreSQL extract result: %s", result)
    return result


def read_delivery_csv(**context):
    """Читает CSV со статусами доставок и группирует их по статусу."""
    if not DELIVERIES_PATH.exists():
        raise FileNotFoundError(f"CSV file not found: {DELIVERIES_PATH}")

    with DELIVERIES_PATH.open(newline="", encoding="utf-8") as csv_file:
        rows = list(csv.DictReader(csv_file))

    status_breakdown = Counter(row["delivery_status"] for row in rows)
    result = {
        "deliveries_count": len(rows),
        "status_breakdown": dict(status_breakdown),
    }

    LOGGER.info("CSV delivery extract result: %s", result)
    return result


def combine_and_analyze(**context):
    """Объединяет результаты извлечения данных и формирует сводную аналитику."""
    ti = context["ti"]
    postgres_result = ti.xcom_pull(task_ids="extract_postgres_data")
    delivery_result = ti.xcom_pull(task_ids="read_delivery_csv")

    total_records = (
        postgres_result["orders_count"]
        + postgres_result["payments_count"]
        + postgres_result["users_count"]
        + delivery_result["deliveries_count"]
    )

    analytics = {
        "total_records": total_records,
        "orders_count": postgres_result["orders_count"],
        "payments_count": postgres_result["payments_count"],
        "users_count": postgres_result["users_count"],
        "deliveries_count": delivery_result["deliveries_count"],
        "paid_revenue": postgres_result["paid_revenue"],
        "delivery_status_breakdown": delivery_result["status_breakdown"],
    }

    LOGGER.info(
        "Marketing batch summary: orders=%s, payments=%s, users=%s, deliveries=%s, paid_revenue=%.2f",
        analytics["orders_count"],
        analytics["payments_count"],
        analytics["users_count"],
        analytics["deliveries_count"],
        analytics["paid_revenue"],
    )
    LOGGER.info("Delivery status breakdown: %s", analytics["delivery_status_breakdown"])
    LOGGER.info("Total processed records: %s", analytics["total_records"])

    return analytics


def choose_processing_branch(**context):
    """Выбирает ветку обработки по общему количеству обработанных записей."""
    analytics = context["ti"].xcom_pull(task_ids="combine_and_analyze")
    total_records = analytics["total_records"]

    if total_records > VOLUME_THRESHOLD:
        LOGGER.info(
            "Total records %s exceeds threshold %s. Using high-volume branch.",
            total_records,
            VOLUME_THRESHOLD,
        )
        return "high_volume_processing"

    LOGGER.info(
        "Total records %s is within threshold %s. Using normal branch.",
        total_records,
        VOLUME_THRESHOLD,
    )
    return "normal_processing"


def normal_processing(**context):
    """Лог. результат обычной ветки обработки небольшого объёма данных."""
    analytics = context["ti"].xcom_pull(task_ids="combine_and_analyze")
    LOGGER.info(
        "Normal processing completed. Prepared marketing batch for %s records.",
        analytics["total_records"],
    )


def high_volume_processing(**context):
    """Лог. результат ветки обработки повышенного объёма данных."""
    analytics = context["ti"].xcom_pull(task_ids="combine_and_analyze")
    LOGGER.info(
        "High-volume processing completed. In production this branch can submit Spark/Kubernetes job. Records=%s",
        analytics["total_records"],
    )


with DAG(
    dag_id="tradeware_marketing_batch_dag",
    description="Batch POC: PostgreSQL + CSV marketing analytics with branching and email notifications.",
    start_date=datetime(2026, 7, 1),
    schedule_interval="@daily",
    catchup=False,
    default_args=default_args,
    tags=["task-1", "batch", "airflow", "marketing"],
) as dag:
    start = EmptyOperator(task_id="start")

    extract_postgres = PythonOperator(
        task_id="extract_postgres_data",
        python_callable=extract_postgres_data,
    )

    read_deliveries = PythonOperator(
        task_id="read_delivery_csv",
        python_callable=read_delivery_csv,
    )

    analyze = PythonOperator(
        task_id="combine_and_analyze",
        python_callable=combine_and_analyze,
    )

    branch = BranchPythonOperator(
        task_id="choose_processing_branch",
        python_callable=choose_processing_branch,
    )

    normal = PythonOperator(
        task_id="normal_processing",
        python_callable=normal_processing,
    )

    high_volume = PythonOperator(
        task_id="high_volume_processing",
        python_callable=high_volume_processing,
    )

    join = EmptyOperator(
        task_id="join_processing_branches",
        trigger_rule=TriggerRule.NONE_FAILED_MIN_ONE_SUCCESS,
    )

    send_success_email = EmailOperator(
        task_id="send_success_email",
        to=["marketing-ops@example.local"],
        subject="Tradeware marketing batch succeeded",
        html_content="""
        <h3>Tradeware marketing batch succeeded</h3>
        <p>The Airflow DAG finished successfully. Check task logs for detailed batch metrics.</p>
        """,
        trigger_rule=TriggerRule.NONE_FAILED_MIN_ONE_SUCCESS,
    )

    send_failure_email = EmailOperator(
        task_id="send_failure_email",
        to=["marketing-ops@example.local"],
        subject="Tradeware marketing batch failed",
        html_content="""
        <h3>Tradeware marketing batch failed</h3>
        <p>One or more upstream tasks failed. Check Airflow task logs for diagnostics.</p>
        """,
        trigger_rule=TriggerRule.ONE_FAILED,
    )

    finish = EmptyOperator(task_id="finish")

    start >> [extract_postgres, read_deliveries] >> analyze >> branch
    branch >> [normal, high_volume] >> join >> send_success_email >> finish
    [extract_postgres, read_deliveries, analyze, branch, normal, high_volume] >> send_failure_email
