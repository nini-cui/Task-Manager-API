from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, HTTPException
import asyncio
import time
from collections import deque

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(
            self,
            app,
            rate_limit: int = 10,
            time_window: int = 60
    ):
        super().__init__(app)
        self.rate_limit = rate_limit
        self.time_window = time_window
        self.ip_ts_mapping = {}
        self.lock = asyncio.Lock()

    async def dispatch(self, request: Request, call_next):
        host_id = request.client.host
        print(f'host id is: {host_id}')

        cur_ts = time.time()
        async with self.lock:
            if host_id not in self.ip_ts_mapping:
                self.ip_ts_mapping[host_id] = deque()
            """
            remove elements that are greater than time window
            then check the length of the queue
            if len > rate limit raise error
            """
            ts_lst = self.ip_ts_mapping[host_id]
            while ts_lst and (cur_ts - ts_lst[0]) > self.time_window:
                ts_lst.popleft()

            if len(ts_lst) > self.rate_limit:
                raise HTTPException(status_code=429, detail="Too many reuqests!")
            
            ts_lst.append(cur_ts)

            response = await call_next(request)
            return response


    
