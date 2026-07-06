from pydantic import BaseModel
from src.eval_workbench.analysis.agreement import AgreementStats
from src.eval_workbench.analysis.comparison import RegressionDetection

class GuardAlert(BaseModel):
    triggered: bool
    reason: str

def check_soul13_guard(
    score_change: RegressionDetection, 
    old_agreement: AgreementStats, 
    new_agreement: AgreementStats
) -> GuardAlert:
    """
    If the metric score went UP on the test split, but human-LLM agreement went DOWN,
    this flags that the model might just be gaming the judge (Goodhart's law),
    or the judge's prompt drifted away from human intent.
    """
    if score_change.is_improvement:
        if new_agreement.kappa is not None and old_agreement.kappa is not None:
            if new_agreement.kappa < old_agreement.kappa - 0.1: # Significant drop in agreement
                return GuardAlert(
                    triggered=True,
                    reason=f"Score improved ({score_change.old_score:.2f} -> {score_change.new_score:.2f}) but human agreement dropped ({old_agreement.kappa:.2f} -> {new_agreement.kappa:.2f})."
                )
    return GuardAlert(triggered=False, reason="OK")
