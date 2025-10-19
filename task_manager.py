import asyncio
import uuid, logging
from models import TaskRequest, TaskType
from exception import InvalidNumberError, ReportGenerationError

class TaskManager:
    def __init__(self, 
                max_workers
                ):
        self.max_workers = max_workers
        self.task_queue = asyncio.Queue()
        self.tasks_status = {}
        self.task_events = {}

    async def submit_task(self, task_request: TaskRequest):
        task_id = str(uuid.uuid4())
        self.tasks_status[task_id] = {
            "status": "queued",
            "parameters": task_request.parameters,
            "result": None,
            "task_type": task_request.task_type
        }
        logging.info(f'task {task_id} created with parameter {task_request.parameters}')
        self.task_events[task_id] = asyncio.Event()
        
        await self.task_queue.put(task_id)

        return task_id
    
    async def process_task(self, task_id):
        self.tasks_status[task_id]["status"] = "processing"
        self.task_events[task_id].set()

        try:
            task_type = self.tasks_status[task_id]["task_type"].value
            print(f"task type is: {task_type}")

            match task_type:
                case "COMPUTE_SUM":
                    # reset the sleep time later
                    await asyncio.sleep(1)
                    numbers = self.tasks_status[task_id]["parameters"].get('numbers')
                    print(f'numbers is: {numbers}')
                    if not numbers or not all([isinstance(num, int) for num in numbers]):
                        raise InvalidNumberError("Invalid numbers")
                    self.tasks_status[task_id]["result"] = sum(numbers)
                case "GENERATE_REPORT":
                    self.tasks_status[task_id]["result"] = f"Report-{uuid.uuid4()}"
                    await asyncio.sleep(3)

            self.tasks_status[task_id]["status"] = "completed"
        except Exception as e:
            self.tasks_status[task_id]["status"] = "failed"
            self.tasks_status[task_id]["result"] = str(e)
        finally:
            self.task_events[task_id].set()
        
        print(f'current tasks_status is: {self.tasks_status}')

    async def worker_loop(self):
        while True:
            tid = await self.task_queue.get()
            print(f'tid is: {tid}')
            await self.process_task(tid)
            self.task_queue.task_done()
            
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

    async def wait_for_task(self, task_id, timeout=10):
        """Wait until task changes status or timeout."""
        event = self.task_events.get(task_id)
        if event:
            try:
                await asyncio.wait_for(event.wait(), timeout=timeout)
            except asyncio.TimeoutError:
                pass  # just return current status
        return self.tasks_status.get(task_id)
      