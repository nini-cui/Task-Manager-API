import asyncio
import uuid, logging
from models import TaskRequest

class TaskManager:
    def __init__(self, 
                max_workers
                ):
        self.max_workers = max_workers
        self.task_queue = asyncio.Queue()
        self.tasks_status = {}

    async def submit_task(self, task_request: TaskRequest):
        task_id = uuid.uuid4()
        self.tasks_status[task_id] = {
            "status": "queued",
            "parameters": task_request.parameters,
            "result": None
        }
        logging.info(f'task {task_id} created with parameter {task_request.parameters}')
        
        await self.task_queue.put(task_id)

        return task_id
    
    async def task_stream(self, status, limit):
        count = 0
        for tid, task in self.tasks_status.items():
            if task["status"] == status:
                item = {
                    "task_id": tid,
                    "status": task["status"],
                    "parameters": task["parameters"],
                    "result": task["resul"]
                }

                yield f"{item}"
                
                count += 1
                if count >= limit:
                    break
        