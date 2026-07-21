from enum import Enum

from pydantic import BaseModel


class TaskType(str, Enum):
    GENERATE_TRACES = "generate_traces"
    GENERATE_TRACE = "generate_trace"
    EVALUATE_TRACES = "evaluate_traces"
    EVALUATE_TRACE = "evaluate_trace"
    RUN_CAMPAIGN = "run_campaign"
    SCAN_AGENT = "scan_agent"


class TaskStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class TaskProgress(BaseModel):
    done: int = 0
    total: int = 0


class Task(BaseModel):
    id: str
    type: TaskType
    status: TaskStatus
    label: str
    progress: TaskProgress | None = None
    error: str | None = None
