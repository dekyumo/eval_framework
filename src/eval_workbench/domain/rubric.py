from typing import Literal
from pydantic import BaseModel
from src.eval_workbench.domain.result import ResultType

class RubricItem(BaseModel):
    name: str
    type: ResultType
    enum_values: list[str] | None = None
    prompt: str = ""                         # objective, anchored ("did the reply cite the refund window?")

class Rubric(BaseModel):
    id: str
    name: str
    instructions: str = ""
    items: list[RubricItem]
    default_judge_prompt: str
    judge_model_id: str = "gemini-2.5-flash" # which model to use as the judge
    consumes_two_traces: bool = False        # pairwise rubric
    version: int
    fingerprint: str
    frozen: bool = False                     # True once any trace has been scored against it
