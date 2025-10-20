# Task Manager API

A simple asynchronous Task Manager API built with FastAPI. Supports submitting tasks, polling for results, cancelling tasks, and rate-limiting.

## Getting Started

1. **Clone the repository**

```bash
git clone <repo-url>
cd Task-Manager-API
```

2. **Create a virtual environment and install dependencies**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. **Run the application**
```bash
uvicorn app.main:app --reload
```

## API Endpoints
1. **Submit task**
```bash
curl -X POST "http://127.0.0.1:8000/tasks" -H "Content-Type: application/json" -d '{"parameters": {"numbers":[5]}, "task_type": "COMPUTE_SUM"}'
```

2. **Get all tasks - need to pass tasks status**
```bash
curl "http://127.0.0.1:8000/tasks?status=completed"
```

3. **Get task**
```bash
curl "http://127.0.0.1:8000/tasks/<task_id>"
```

4. **Cancel task**
```bash
curl -X DELETE "http://127.0.0.1:8000/tasks/d7e6bd89-1672-4c85-b084-d733c92e75b6"
```