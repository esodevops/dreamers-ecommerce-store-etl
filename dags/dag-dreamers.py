import os
import sys
from pathlib import Path
from datetime import timedelta

import pendulum
from airflow import DAG
from airflow.providers.smtp.notifications.smtp import send_smtp_notification
from airflow.providers.standard.operators.python import PythonOperator

# Add the project folder so Airflow can find the src package.
PROJECT_FOLDER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_FOLDER)


from src.extraction import extraction
from src.loading import loading
from src.transformation import transformation


ALERT_EMAIL = os.getenv("AIRFLOW_ALERT_EMAIL")


dag_failure_notification = send_smtp_notification(
    smtp_conn_id="smtp_default",
    from_email=ALERT_EMAIL,
    to=ALERT_EMAIL,
    subject="[Airflow] Task {{ ti.task_id }} failed",
    html_content="""
        <p>DAG <strong>{{ dag.dag_id }}</strong> failed.</p>
        <p>Run: {{ run_id }}</p>
        <p>Failed task: {{ ti.task_id }}</p>
        <p><a href="{{ ti.log_url }}">View task logs</a></p>
    """,
)

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=1),
    "on_failure_callback": [dag_failure_notification],
}


with DAG(
    dag_id="dreamers_ecommerce_dag",
    default_args=default_args,
    description="Dreamers ecommerce batch ETL pipeline",
    start_date=pendulum.datetime(2026, 8, 17, tz="Europe/Helsinki"),
    schedule=None,
    catchup=False,
    tags=["dreamers", "ecommerce", "etl"],
) as dag:

    extraction_task = PythonOperator(
        task_id="extraction_layer",
        python_callable=extraction,
        do_xcom_push=False,
    )

    transformation_task = PythonOperator(
        task_id="transformation_layer",
        python_callable=transformation,
        do_xcom_push=False,
    )

    loading_task = PythonOperator(
        task_id="loading_layer",
        python_callable=loading,
        do_xcom_push=False,
    )

    extraction_task >> transformation_task >> loading_task
