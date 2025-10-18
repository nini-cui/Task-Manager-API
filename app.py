from fastapi import FastAPI, HTTPException
import uvicorn
from models import TaskRequest
from task_manager import TaskManager
from typing import Optional
from fastapi.responses import StreamingResponse

app = FastAPI()
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
                    "result": task["resul"]
                } 
                for tid, task in task_manager.tasks_status.items if task["status"] == status
            ]

            return {"tasks": tasks}
        elif len(task_manager.tasks_status) > limit:
            return StreamingResponse(task_manager.task_stream(status, limit), )
    # else return all data or set a threashold

if __name__ == "__main__":
    uvicorn.run(app, port=8000)