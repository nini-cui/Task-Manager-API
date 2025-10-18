from pydantic import BaseModel
from enum import Enum

class TaskType(Enum):
    COMPUTE_SUM = "COMPUTE_SUM"
    GENERATEREPORT = "GENERATE_REPORT"

class TaskRequest(BaseModel):
    task_type: TaskType
    parameters: dict