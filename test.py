import asyncio

async def worker(worker_id, queue):
    while True:
        task = await queue.get()
        print(f'current task is: {task}')
        if task is None:  # Stop signal
            print(f"Worker {worker_id} exiting")
            break
        print(f"Worker {worker_id} processing {task}")
        await asyncio.sleep(1)  # Simulate async work
        queue.task_done()

async def main():
    queue = asyncio.Queue()

    # Add tasks
    for i in range(10):
        await queue.put(f"task-{i}")
    print(f"current queue is: {queue}")
    # Create 3 workers
    workers = [asyncio.create_task(worker(i, queue)) for i in range(3)]

    # Wait for all tasks to finish
    await queue.join()

    # Stop all workers
    for _ in range(len(workers)):
        await queue.put(None)

    # Wait for workers to finish
    await asyncio.gather(*workers)

asyncio.run(main())
