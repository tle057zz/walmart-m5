FROM apache/airflow:2.10.5

# Keep the default airflow user so /home/airflow/.local/bin stays on PATH.
USER airflow
RUN pip install --no-cache-dir "apache-airflow-providers-databricks==6.12.0"
