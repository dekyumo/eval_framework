from pydantic import BaseModel
from src.eval_workbench.domain.trace import Trace
from src.eval_workbench.domain.result import Result, AggregateResult

class EvalRun(BaseModel):
    id: str
    snapshot_id: str
    case_id: str
    model_id: str                            # may differ from snapshot default in a campaign
    repetition_index: int
    trace: Trace
    campaign_id: str | None = None

class ScoredEvalRun(BaseModel):
    id: str
    run_id: str
    results: list[Result]
    aggregates: list[AggregateResult] = []   # when folded across repetitions
