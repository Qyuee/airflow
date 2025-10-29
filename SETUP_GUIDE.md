# Airflow 3.1.1 프로젝트 설정 완전 가이드

지금까지 진행한 모든 작업을 시간순으로 정리했습니다.

---

## 1. 초기 문제: uv sync 의존성 설치 실패

### 문제 상황
```
× Failed to build `pendulum==2.1.2`
ModuleNotFoundError: No module named 'distutils'
```

**원인**:
- 초기 `pyproject.toml`에 `apache-airflow==2.7.3` 설정
- Python 3.13 환경에서 실행
- `pendulum==2.1.2`가 Python 3.12+에서 제거된 `distutils` 모듈 필요

---

## 2. 첫 번째 해결 시도: Airflow 2.11.0으로 업그레이드

### 시도한 작업
```toml
# pyproject.toml
requires-python = ">=3.8"
dependencies = ["apache-airflow==2.11.0", ...]
```

### 새로운 문제 발생
```
apache-airflow==2.11.0 depends on Python>=3.9,<3.13
```

**해결**: `requires-python = ">=3.9,<3.13"` 수정
- Python 3.9로 설치 성공
- Airflow 2.11.0 정상 작동

---

## 3. 버전 통일 결정: Docker와 로컬 환경

### 상황
- Docker: `apache/airflow:3.1.1` 사용 중
- 로컬: Airflow 2.11.0 설치됨
- DAG 파일에서 import 오류 발생
  ```python
  ModuleNotFoundError: No module named 'airflow.providers.mysql.operators'
  ```

### 결정
**"로컬 환경을 Docker에 맞춰 3.1.1로 업그레이드"**

---

## 4. Airflow 3.1.1 설치 시도 및 문제들

### 문제 1: Python 버전 호환성
```
apache-airflow==3.1.1 depends on Python>=3.10,<3.14
```

**해결**: `requires-python = ">=3.10,<3.14"` 수정

### 문제 2: structlog 호환성 이슈
```python
ImportError: cannot import name 'Styles' from 'structlog.dev'
```

**원인**:
- Python 3.13 사용 시 structlog 25.5.0 자동 설치
- Airflow 3.1.1과 structlog 최신 버전 간 호환성 문제

### 최종 해결
```toml
# pyproject.toml
requires-python = ">=3.10,<3.13"  # Python 3.12로 제한
dependencies = [
    "apache-airflow==3.1.1",
    "structlog==25.4.0",  # 호환 버전 고정
    ...
]
```

✅ **Python 3.12 + Airflow 3.1.1 + structlog 25.4.0 조합으로 성공!**

---

## 5. DAG 파일 Airflow 3.x 호환 업데이트

### 변경 사항 (dags/sample.py)

#### Import 경로 변경
```python
# Before (Airflow 2.x)
from airflow.operators.python import PythonOperator
from airflow.providers.mysql.operators.mysql import MySqlOperator

# After (Airflow 3.x)
from airflow.providers.standard.operators.python import PythonOperator
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator
```

#### Operator 변경
```python
# Before
check_tables = MySqlOperator(
    task_id='check_table_count',
    mysql_conn_id='local_mysql',  # 파라미터명
    sql="...",
)

# After
check_tables = SQLExecuteQueryOperator(
    task_id='check_table_count',
    conn_id='local_mysql',  # 파라미터명 변경
    sql="...",
)
```

#### DAG 파라미터 변경
```python
# Before
with DAG(
    'dag_id',
    schedule_interval='@daily',  # 구버전
    ...
)

# After
with DAG(
    'dag_id',
    schedule='@daily',  # 신버전
    ...
)
```

---

## 6. Docker 설정: 호스트 MySQL 연결

### 문제
Docker 컨테이너에서 호스트 서버의 localhost MySQL 접근 필요

### 해결 (docker-compose.yaml:83-84)
```yaml
x-airflow-common:
  &airflow-common
  volumes:
    - ...
  user: "${AIRFLOW_UID:-50000}:0"
  extra_hosts:  # 추가!
    - "host.docker.internal:host-gateway"
```

### MySQL Connection 설정
**Airflow UI에서:**
- Connection Id: `mysql_localhost`
- Connection Type: `MySQL`
- Host: `host.docker.internal` ⭐
- Schema: 데이터베이스명
- Login: 사용자명
- Password: 비밀번호
- Port: `3306`

---

## 7. Git 저장소 설정

### .gitignore 작성
```gitignore
# Python
__pycache__/
*.pyc
.venv/

# Airflow
logs/
airflow.db
*.pid

# 민감 정보
.env

# IDE
.idea/
.vscode/
```

### GitHub Repository Push
```bash
git init
git add .
git commit -m "Initial commit: Airflow 3.1.1 project setup"
git remote add origin https://github.com/Qyuee/airflow.git
git push -u origin main
```

---

## 8. GitDagBundle 설정

### GitHub Token 발급
**필요한 권한:**
- Fine-grained Token (권장)
  - Repository access: `Qyuee/airflow`
  - Contents: **Read-only**
  - Metadata: **Read-only**

### 환경 변수 설정 (.env:3-11)
```bash
# GitHub Connection
AIRFLOW_CONN_GITHUB_DEFAULT=git://github.com/Qyuee/airflow?token=github_pat_xxx

# GitDagBundle Configuration
AIRFLOW__DAG_BUNDLES__GITHUB_DAGS__URL=https://github.com/Qyuee/airflow.git
AIRFLOW__DAG_BUNDLES__GITHUB_DAGS__BRANCH=main
AIRFLOW__DAG_BUNDLES__GITHUB_DAGS__SUBDIR=dags
AIRFLOW__DAG_BUNDLES__GITHUB_DAGS__CONNECTION_ID=github_default
```

### 예제 DAG 생성
`dags/git_dag_bundle_example.py` - GitHub에서 자동 동기화되는 DAG 예제

---

## 최종 프로젝트 구조

```
airflow/
├── .env                          # 환경 변수 (Git 제외)
├── .gitignore                    # Git 제외 파일 목록
├── docker-compose.yaml           # Airflow 3.1.1 Docker 설정
├── pyproject.toml                # Python 3.10-3.12, Airflow 3.1.1
├── uv.lock                       # 의존성 락 파일
├── SETUP_GUIDE.md                # 이 파일
├── dags/
│   ├── sample.py                 # MySQL DAG (3.x 호환)
│   ├── dag_versioning_example.py # Task SDK 예제
│   └── git_dag_bundle_example.py # GitDagBundle 예제
├── logs/                         # Airflow 로그 (Git 제외)
├── plugins/                      # Airflow 플러그인
└── config/
    └── airflow.cfg               # Airflow 설정 (자동 생성)
```

---

## 주요 버전 정보

| 컴포넌트 | 버전 | 비고 |
|---------|------|------|
| Python | 3.12 | 3.10-3.12 지원 |
| Apache Airflow | 3.1.1 | Docker와 동일 |
| structlog | 25.4.0 | 호환성 문제로 고정 |
| MySQL Provider | 6.3.4 | 자동 설치 |
| Docker Image | apache/airflow:3.1.1 | |

---

## 핵심 교훈 및 우회 방법

### 1. Python 버전 호환성
- ❌ Python 3.13: distutils 제거로 구버전 패키지 빌드 실패
- ❌ Python 3.9: Airflow 3.x 지원 안 함
- ✅ Python 3.12: Airflow 3.1.1과 완벽 호환

### 2. 패키지 버전 고정의 중요성
```toml
structlog==25.4.0  # ">=25.4.0" 사용 시 25.5.0 설치되어 문제 발생
```

### 3. Airflow 2.x → 3.x 주요 변경사항
- `schedule_interval` → `schedule`
- `MySqlOperator` → `SQLExecuteQueryOperator`
- `mysql_conn_id` → `conn_id`
- Import 경로 변경 (`airflow.operators` → `airflow.providers.standard.operators`)

### 4. Docker 네트워킹
- 컨테이너에서 호스트 접근: `host.docker.internal`
- `extra_hosts` 설정 필수 (특히 Linux)

---

## 빠른 시작 가이드

### 1. 프로젝트 클론
```bash
git clone https://github.com/Qyuee/airflow.git
cd airflow
```

### 2. 환경 변수 설정
`.env` 파일 생성:
```bash
AIRFLOW_UID=501

# MySQL Connection (선택사항)
AIRFLOW_CONN_MYSQL_LOCALHOST=mysql://user:password@host.docker.internal:3306/database

# GitHub Connection (GitDagBundle 사용 시)
AIRFLOW_CONN_GITHUB_DEFAULT=git://github.com/Qyuee/airflow?token=YOUR_TOKEN

# GitDagBundle Configuration
AIRFLOW__DAG_BUNDLES__GITHUB_DAGS__URL=https://github.com/Qyuee/airflow.git
AIRFLOW__DAG_BUNDLES__GITHUB_DAGS__BRANCH=main
AIRFLOW__DAG_BUNDLES__GITHUB_DAGS__SUBDIR=dags
AIRFLOW__DAG_BUNDLES__GITHUB_DAGS__CONNECTION_ID=github_default
```

### 3. 로컬 개발 환경 설정
```bash
# uv를 사용한 의존성 설치
uv sync

# 가상환경 활성화
source .venv/bin/activate

# Airflow 버전 확인
airflow version  # 3.1.1
```

### 4. Docker 환경 시작
```bash
# Airflow 시작
docker compose up -d

# 서비스 상태 확인
docker compose ps

# 로그 확인
docker compose logs -f
```

### 5. Airflow UI 접속
- URL: http://localhost:8080
- Username: `airflow`
- Password: `airflow`

---

## 문제 해결 (Troubleshooting)

### DAG가 UI에 나타나지 않을 때
```bash
# DAG 파일 문법 검사
python dags/your_dag.py

# DAG processor 로그 확인
docker compose logs airflow-dag-processor --tail 50

# DAG 파일 권한 확인
ls -la dags/
```

### MySQL 연결 실패 시
```bash
# 호스트에서 MySQL 실행 확인
mysql -u root -p

# MySQL이 외부 연결을 허용하는지 확인
# /etc/mysql/mysql.conf.d/mysqld.cnf
# bind-address = 0.0.0.0

# Docker 컨테이너에서 호스트 접근 테스트
docker compose exec airflow-worker ping host.docker.internal
```

### GitDagBundle 동기화 안 될 때
```bash
# GitHub connection 확인
docker compose exec airflow-apiserver airflow connections get github_default

# DAG processor 로그에서 에러 확인
docker compose logs airflow-dag-processor | grep -i error

# GitHub token 권한 확인 (Contents: Read 필요)
```

---

## 다음 단계 제안

1. ✅ Airflow UI에서 DAG 확인 (http://localhost:8080)
2. ✅ MySQL connection 테스트
3. ✅ GitDagBundle 동기화 확인 (5분마다 자동)
4. 📝 `.env.example` 파일 생성 (팀원 공유용)
5. 📝 프로덕션 환경 설정 검토
6. 📝 모니터링 및 알림 설정

---

## 참고 자료

- [Apache Airflow 3.x Documentation](https://airflow.apache.org/docs/apache-airflow/3.1.1/)
- [Airflow Providers MySQL](https://airflow.apache.org/docs/apache-airflow-providers-mysql/stable/)
- [GitDagBundle Documentation](https://airflow.apache.org/docs/apache-airflow/stable/administration-and-deployment/dag-bundles.html)
- [Docker Compose for Airflow](https://airflow.apache.org/docs/apache-airflow/stable/howto/docker-compose/index.html)

---

**작성일**: 2025-10-29
**Airflow 버전**: 3.1.1
**Python 버전**: 3.12

---

이 가이드는 실제 설정 과정에서 발생한 모든 문제와 해결 방법을 포함하고 있습니다.