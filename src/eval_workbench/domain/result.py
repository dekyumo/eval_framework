from typing import Literal
from pydantic import BaseModel

ResultType = Literal["bool", "int", "float", "enum"]
ResultSource = Literal["deterministic", "verifier", "llm_judge", "human"]
Confidence = Literal["low", "medium", "high"]

class Result(BaseModel):
    name: str                                # which metric / rubric item
    type: ResultType
    value: bool | int | float | str          # str only when type == "enum"
    enum_values: list[str] | None = None     # required when type == "enum"
    confidence: Confidence | None = None      # judges/humans set this; deterministic may omit
    rationale: str | None = None
    traceback: str | None = None             # set if an extractor crashes during evaluation
    source: ResultSource

class AggregateResult(BaseModel):
    name: str
    type: ResultType
    n: int
    stats: dict                              # shape depends on type (see folds)
