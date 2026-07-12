import logging
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path

import psycopg2


LOG_FORMAT = "%(asctime)s %(levelname)s %(message)s"


class CountingWriter:
    def __init__(self, file_handle):
        self.file_handle = file_handle
        self.line_count = 0

    def write(self, data: str) -> int:
        self.line_count += data.count("\n")
        return self.file_handle.write(data)


def get_required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise ValueError(f"Required environment variable {name} is not set")
    return value


def export_shipments() -> int:
    logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)

    db_host = get_required_env("DB_HOST")
    db_port = get_required_env("DB_PORT")
    db_name = get_required_env("DB_NAME")
    db_user = get_required_env("DB_USER")
    db_password = get_required_env("DB_PASSWORD")
    export_dir = Path(get_required_env("EXPORT_DIR"))

    logging.info("Starting shipments export")
    logging.info(
        "Database connection parameters: host=%s port=%s dbname=%s user=%s export_dir=%s",
        db_host,
        db_port,
        db_name,
        db_user,
        export_dir,
    )

    export_dir.mkdir(parents=True, exist_ok=True)
    file_name = f"shipments_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    output_path = export_dir / file_name

    connection = None
    row_count = 0

    try:
        connection = psycopg2.connect(
            host=db_host,
            port=db_port,
            dbname=db_name,
            user=db_user,
            password=db_password,
        )

        with connection:
            with connection.cursor() as cursor:
                logging.info("Exporting shipments table with COPY TO STDOUT")
                copy_sql = """
                    COPY (
                        SELECT
                            id,
                            tracking_number,
                            origin_city,
                            destination_city,
                            status,
                            weight_kg,
                            price_amount,
                            created_at
                        FROM shipments
                        ORDER BY id
                    ) TO STDOUT WITH CSV HEADER
                """

                with output_path.open("w", encoding="utf-8", newline="") as csv_file:
                    counting_writer = CountingWriter(csv_file)
                    cursor.copy_expert(copy_sql, counting_writer)
                    row_count = max(counting_writer.line_count - 1, 0)

        logging.info("Exported rows: %s", row_count)
        logging.info("CSV file path: %s", output_path)
        logging.info("Shipments export finished successfully")
        return 0

    except Exception: # noqa
        logging.error("Shipments export failed")
        logging.error("Stacktrace:\n%s", traceback.format_exc())
        return 1

    finally:
        if connection is not None:
            connection.close()


if __name__ == "__main__":
    sys.exit(export_shipments())
