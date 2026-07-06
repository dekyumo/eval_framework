from pydantic import BaseModel
from src.eval_workbench.domain.result import ResultType

class Extractor(BaseModel):
    id: str
    name: str
    return_type: ResultType
    source_path: str                         # inspectable .py, authored/edited by a human (AGENT4 drafts)
    fingerprint: str                         # sha256 of normalized source
