from typing import Literal, Any
from pydantic import BaseModel

FaultBoundary = Literal["user_input","tool_call","tool_result","model_transport","model_output","state","inter_agent"]
FaultClass = Literal["crash","omission","timing","value","byzantine"]
FaultTrigger = Literal["first_call","nth_call","always"]

ToolFaultType = Literal[
    "availability",
    "performance",
    "interface",
    "correctness",
    "partial_failure",
    "determinism",
    "ordering",
    "consistency",
    "precision",
    "semantics",
    "security",
    "state",
    "resource",
    "authorization",
    "side_effects",
    "observability",
]


class ToolFault(BaseModel):
    tool_name: str
    fault_type: ToolFaultType


class FaultConfig(BaseModel):
    id: str
    boundary: FaultBoundary
    fault_class: FaultClass
    target: str                              # tool name, or "model"
    trigger: FaultTrigger = "always"
    n: int | None = None                     # for nth_call
    persistent: bool = True                  # transient (recover by retry) vs persistent (escalate)
    payload: Any | None = None               # garbage value / http code / malformed body
    seed: int = 0                            # deterministic
    mocked_tools_ref: str                    # path to mocked_tools.py
    mocked_tools_fingerprint: str
