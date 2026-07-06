from pydantic import BaseModel
from src.eval_workbench.domain.result import Result

class HumanEval(BaseModel):
    id: str
    run_id: str
    rubric_id: str
    results: list[Result]                    # same structure as automated; source="human"
    comments: str = ""
