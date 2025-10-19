import asyncio
import uuid, logging
from models import TaskRequest
from exception import InvalidNumberError, ReportGenerationError

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
            "result": None,
            "task_type": task_request.task_type
        }
        logging.info(f'task {task_id} created with parameter {task_request.parameters}')
        
        await self.task_queue.put(task_id)

        return task_id
    
    async def process_task(self, task_id):
        self.tasks_status[task_id]["status"] == "processing"

        try:
            task_type = self.tasks_status[task_id]["task_type"]
            print(f"task type is: {task_type}")

            match task_type:
                case "COMPUTE_SUM":
                    asyncio.sleep(5)
                    numbers = self.tasks_status["parameters"].get('numbers')
                    if not numbers or not all([isinstance(num, int) for num in numbers]):
                        raise InvalidNumberError("Invalid numbers")
                    res = sum(numbers)
                case "GENERATE_REPORT":
                    res = f"Report-{uuid.uuid4()}"
                    asyncio.sleep(5)

            self.tasks_status[task_id]["status"] = "completed"
            self.tasks_status[task_id]["result"] = res
        except Exception as e:
            self.tasks_status[task_id]["status"] == "failed"
            self.tasks_status[task_id]["result"] = str(e)
    
    async def task_stream(self, status):
        for tid, task in self.tasks_status.items():
            if task["status"] == status:
                item = {
                    "task_id": tid,
                    "status": task["status"],
                    "parameters": task["parameters"],
                    "result": task["result"]
                }

                yield f"{item}"
                await asyncio.sleep(0)
      