import asyncio, time, uuid, logging
from models import TaskRequest
from exception import InvalidNumberError
from fastapi import HTTPException

class TaskManager:
    def __init__(self, 
                max_workers
                ):
        self.max_workers = max_workers
        self.task_queue = asyncio.Queue(maxsize=100)
        self.tasks_status = {}
        self.task_events = {}

        # params for cleanup task
        self.cleanup_interval = 60
        self.task_ttl = 600

    async def submit_task(self, task_request: TaskRequest):
        task_id = str(uuid.uuid4())
        self.tasks_status[task_id] = {
            "status": "queued",
            "parameters": task_request.parameters,
            "result": None,
            "task_type": task_request.task_type,
            "created_time": time.time()
        }
        logging.info(f'task {task_id} created with parameter {task_request.parameters}')
        self.task_events[task_id] = asyncio.Event()

        try:
            self.task_queue.put_nowait(task_id)
        except asyncio.QueueFull:
            raise HTTPException(status_code=503, detail="Task queue full, try again later")

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
            tasks_to_process = []
            for _ in range(self.max_workers):
                tid = await self.task_queue.get()
                print(f'tid is: {tid}')

                if self.tasks_status[tid]['status'] != "cancelled":
                    tasks_to_process.append(tid)

            if tasks_to_process:
                try:
                    await self.process_task(tid)
                except asyncio.CancelledError:
                    logging.info("Task cancelled successfully!")
                    break
            
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
    
    async def cancel_task(self, task_id: str):
        if task_id not in self.tasks_status:
            return False

        status = self.tasks_status[task_id]["status"]
        if status != "queued":
            return False

        # Mark as cancelled
        self.tasks_status[task_id]["status"] = "cancelled"
        self.tasks_status[task_id]["result"] = None

        # Notify anyone waiting
        if task_id in self.task_events:
            self.task_events[task_id].set()

        print(f"Task {task_id} marked as cancelled (still in queue)")
        return True
    
    async def cleanup_task(self):
        while True:
            cur_ts = time.time()

            task_to_delete = []

            for tid, task in self.tasks_status.items():
                if (task["status"] in ("completed", "failed", "cancelled")) and (cur_ts - task["created_time"] > self.task_ttl):
                    task_to_delete.append(tid)

            if task_to_delete:
                # pop from tasks_status list
                logging.info(f"cleaning up task: {tid}")
                for tid in task_to_delete:
                    self.tasks_status.pop(tid, None)
                    self.task_events.pop(tid, None)

            await asyncio.sleep(self.cleanup_interval)

    
    
      