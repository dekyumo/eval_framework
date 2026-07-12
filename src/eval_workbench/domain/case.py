from typing import Literal, Any, Self
from pydantic import BaseModel, model_validator
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

class AgenticUserConfig(BaseModel):
    """Turns a case into a two-agent gym simulation (tau-bench style).

    A user agent and the solver agent take turns until the gym's termination
    method returns True or `max_turns` is reached. Gym bound methods named in
    `user_tools` / `solver_tools` are injected as tools into each agent.
    """

    user_agent_path: str                     # "module.path:variable" for the simulated user
    gym_ref: str = ""                        # -> Gym.id (optional if gym_class_path set)
    gym_class_path: str | None = None        # direct FQCN override, e.g. gym.foo_gym.FooGym
    user_tools: list[str] = []               # gym method names given to the user agent
    solver_tools: list[str] = []             # gym method names given to the solver agent
    max_turns: int = 10
    termination_method: str                  # gym method name returning bool

    @model_validator(mode="after")
    def gym_source_required(self) -> Self:
        if not self.gym_class_path and not self.gym_ref:
            raise ValueError("agentic_user requires gym_ref or gym_class_path")
        return self

class EvalCase(BaseModel):
    id: str
    name: str = ""
    logical_id: str = ""
    version: int = 1
    active_for_eval: bool = True
    dataset_id: str
    conversation: list[MessagePart] = []     # multi-turn input (agentic, not single prompt)
    session_state: dict[str, Any] | None = None   # injected into ADK session state before run; reserved key "gym" configures the gym
    input_payload: dict[str, Any] | None = None   # structured new_message JSON (mutually exclusive with conversation)
    agentic_user: AgenticUserConfig | None = None  # if set, run a gym simulation instead of a fixed conversation
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
