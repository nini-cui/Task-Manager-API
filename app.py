from fastapi import FastAPI, HTTPException
import uvicorn, asyncio
from models import TaskRequest
from task_manager import TaskManager
from typing import Optional
from fastapi.responses import StreamingResponse
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    for _ in range(task_manager.max_workers):
        asyncio.create_task(task_manager.worker_loop())
    print("Background worker started")
    yield 
    print("App shutting down")

app = FastAPI(lifespan=lifespan)
task_manager = TaskManager(max_workers=5)

@app.post('/tasks', status_code=202)
async def submit_task(task_request: TaskRequest):
    # data validation
    if 'numbers' not in task_request.parameters:
        raise HTTPException(status_code=400, detail="Numbers must be provided!")
    if not all(isinstance(num, int) for num in task_request.parameters['numbers']):
        raise HTTPException(status_code=400, detail="numbers have to be type of integer!")

    task_id = await task_manager.submit_task(task_request)
    return {"task_id": task_id, "status": "queued"}

@app.get('/tasks')
async def get_tasks(status: Optional[str] = None, limit: Optional[int] = None):
    if limit:
        if len(task_manager.tasks_status) <= limit:
            tasks = [
                {
                    "task_id": tid,
                    "status": task["status"],
                    "parameters": task["parameters"],
                    "result": task["result"]
                } 
                for tid, task in task_manager.tasks_status.items() if task["status"] == status
            ]

            return {"tasks": tasks}
        
    return StreamingResponse(task_manager.task_stream(status), media_type='text/plain')

@app.get('/tasks/{task_id}')
async def get_task(task_id: str, wait: bool = None):
    if task_id not in task_manager.tasks_status:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task_manager.tasks_status[task_id]["status"] in ('queued', 'processing') and wait:
        task = task_manager.wait_for_task(task_id)
    else:
        task = task_manager.tasks_status[task_id]

    return {"status": task["status"], "result": task["result"]}

@app.delete("/tasks/{task_id}")
async def cancel_task(task_id: str):
    task = task_manager.tasks_status[task_id]
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    cancelled = await task_manager.cancel_task(task_id)
    if not cancelled:
        raise HTTPException(status_code=400, detail="Task already processing or completed")
    
    return {"task_id": task_id, "status": "cancelled"}

if __name__ == "__main__":
    uvicorn.run(app, port=8000)