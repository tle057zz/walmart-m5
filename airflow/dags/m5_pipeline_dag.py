"""Walmart M5 pipeline DAG — local validation then Databricks Medallion job."""

from __future__ import annotations

import os

import pendulum
from airflow import DAG
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import PythonOperator
from airflow.providers.databricks.operators.databricks import DatabricksRunNowOperator

from src.ingestion.airflow_tasks import (
    check_source_files,
    record_databricks_run,
    validate_raw_files,
)

default_args = {
    "owner": "walmart-m5",
    "retries": 1,
    "retry_delay": pendulum.duration(minutes=2),
}

DATABRICKS_JOB_ID = os.environ.get("WALMART_M5_DATABRICKS_JOB_ID", "").strip()
try:
    DATABRICKS_JOB_ID_TYPED: int | str = int(DATABRICKS_JOB_ID)
except ValueError:
    DATABRICKS_JOB_ID_TYPED = DATABRICKS_JOB_ID

with DAG(
    dag_id="m5_pipeline",
    description="Validate local M5 sources, then run Databricks Bronze→Silver→Gold job",
    default_args=default_args,
    start_date=pendulum.datetime(2026, 9, 1, tz="UTC"),
    schedule=None,  # trigger manually while developing
    catchup=False,
    tags=["walmart-m5", "databricks", "medallion"],
) as dag:
    start = EmptyOperator(task_id="start")
    end = EmptyOperator(task_id="end")

    check_sources = PythonOperator(
        task_id="check_source_files",
        python_callable=check_source_files,
    )

    validate_raw = PythonOperator(
        task_id="validate_raw_files",
        python_callable=validate_raw_files,
    )

    # Requires:
    # 1) Airflow connection `databricks_default` (see airflow/.env.example)
    # 2) env WALMART_M5_DATABRICKS_JOB_ID = Databricks Job ID
    run_medallion = DatabricksRunNowOperator(
        task_id="run_databricks_medallion",
        databricks_conn_id="databricks_default",
        job_id=DATABRICKS_JOB_ID_TYPED,
        wait_for_termination=True,
        deferrable=False,
    )

    record_success = PythonOperator(
        task_id="record_databricks_success",
        python_callable=record_databricks_run,
        op_kwargs={"job_id": str(DATABRICKS_JOB_ID_TYPED)},
    )

    (
        start
        >> check_sources
        >> validate_raw
        >> run_medallion
        >> record_success
        >> end
    )
