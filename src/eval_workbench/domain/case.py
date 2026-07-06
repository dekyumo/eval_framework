from typing import Literal, Any
from pydantic import BaseModel
from src.eval_workbench.domain.trace import MessagePart
from src.eval_workbench.domain.result import ResultType
from src.eval_workbench.domain.fault import FaultConfig, ToolFault

MetricStrategy = Literal["deterministic", "verifier", "rubric"]
DistributionPosition = Literal["in", "margin", "ood"]
ProblemType = Literal["happy", "technical", "adversarial", "client"]
Split = Literal["train", "test"]
CaseSource = Literal["manual", "generated", "copied", "incident"]

class MetricDef(BaseModel):
    id: str
    name: str
    strategy: MetricStrategy
    result_type: ResultType
    enum_values: list[str] | None = None
    # deterministic: extractor + ground truth
    extractor_ref: str | None = None         # -> Extractor.id
    ground_truth: Any | None = None
    comparator: str | None = None            # "eq", "abs_tol:0.01", "in_set", ...
    # verifier: external function/program
    verifier_ref: str | None = None
    # rubric
    rubric_ref: str | None = None            # -> Rubric.id

class EvalCase(BaseModel):
    id: str
    name: str = ""
    target_agent_path: str                   # WHICH agent in the repo this case targets (root or a sub-agent)
    conversation: list[MessagePart] = []     # multi-turn input (agentic, not single prompt)
    session_state: dict[str, Any] | None = None   # injected into ADK session state before run
    input_payload: dict[str, Any] | None = None   # structured new_message JSON (mutually exclusive with conversation)
    distribution_position: DistributionPosition          # coverage attribute of THIS case (in / margin / ood)
    problem_type: ProblemType
    tags: list[str] = []
    metrics: list[MetricDef] = []            
    fault_config: FaultConfig | None = None
    tool_fault: ToolFault | None = None
    split: Split = "test"                 # SOUL13; default held-out
    difficulty_prior: Literal["easy", "medium", "hard"] | None = None  # derived from distribution_position x problem
    source: CaseSource = "manual"

class EvalDataset(BaseModel):
    id: str
    name: str
    case_ids: list[str]
