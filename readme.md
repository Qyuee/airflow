# docker-compose.yaml 다운로드
curl -LfO 'https://airflow.apache.org/docs/apache-airflow/stable/docker-compose.yaml'

# 환경 설정
mkdir -p ./dags ./logs ./plugins ./config
echo -e "AIRFLOW_UID=$(id -u)" > .env

# 초기화
docker compose up airflow-init

# 실행
docker compose up