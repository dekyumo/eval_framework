from pydantic import BaseModel

class EvalCampaign(BaseModel):
    id: str
    name: str
    dataset_id: str
    base_snapshot_id: str                    # FIXED agent code/prompt; only the model varies
    model_panel: list[str]                   # e.g. gemini-2.5-flash ...
    repetitions: int = 1
    created_at: float
