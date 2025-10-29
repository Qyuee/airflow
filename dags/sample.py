# dags/local_mysql_query.py
from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator
from airflow.providers.mysql.hooks.mysql import MySqlHook
from datetime import datetime

def query_mysql_database():
    """MySQLHook 사용"""
    hook = MySqlHook(mysql_conn_id='mysql_localhost')
    
    sql = """
        SELECT 
            table_name,
            table_rows
        FROM information_schema.tables
        WHERE table_schema = DATABASE()
        ORDER BY table_rows DESC
        LIMIT 5
    """
    
    results = hook.get_records(sql)
    
    print("=== Top 5 Tables by Row Count ===")
    for table_name, row_count in results:
        print(f"{table_name}: {row_count:,} rows")
    
    return results

with DAG(
    'local_mysql_query_example',
    description='로컬 MySQL 조회 예제',
    schedule='@daily',
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['example', 'mysql'],
) as dag:

    # SQLExecuteQueryOperator 사용 (Airflow 3.x)
    check_tables = SQLExecuteQueryOperator(
        task_id='check_table_count',
        conn_id='mysql_localhost',
        sql="""
            SELECT COUNT(*) as table_count
            FROM information_schema.tables
            WHERE table_schema = DATABASE();
        """,
    )

    # Python Hook 사용
    get_table_stats = PythonOperator(
        task_id='get_table_statistics',
        python_callable=query_mysql_database,
    )

    check_tables >> get_table_stats