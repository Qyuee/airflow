"""
GitDagBundle Example
This DAG demonstrates how to sync DAGs from a GitHub repository.
"""
from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from datetime import datetime


def print_git_info():
    """Print information about GitDagBundle"""
    print("=" * 50)
    print("GitDagBundle Configuration")
    print("=" * 50)
    print("Repository: https://github.com/Qyuee/airflow")
    print("Branch: main")
    print("This DAG is synced from GitHub!")
    print("=" * 50)

    print("version2 - 테스트")


with DAG(
    dag_id='git_dag_bundle_example',
    description='Example DAG using GitDagBundle',
    schedule='@daily',
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['git', 'example'],
) as dag:

    task = PythonOperator(
        task_id='print_git_info',
        python_callable=print_git_info,
    )