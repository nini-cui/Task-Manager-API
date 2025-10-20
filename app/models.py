from pydantic import BaseModel
from enum import Enum

class TaskType(Enum):
    COMPUTE_SUM = "COMPUTE_SUM"
    GENERATE_REPORT = "GENERATE_REPORT"

class TaskRequest(BaseModel):
    task_type: TaskType
    parameters: dict