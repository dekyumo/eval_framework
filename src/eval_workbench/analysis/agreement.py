import numpy as np
from sklearn.metrics import confusion_matrix, cohen_kappa_score
from pydantic import BaseModel
from src.eval_workbench.domain.result import Result

class AgreementStats(BaseModel):
    rubric_item_name: str
    item_type: str
    n: int
    kappa: float | None = None
    confusion_matrix: list[list[int]] | None = None
    correlation: float | None = None

def calculate_agreement(human_results: list[Result], llm_results: list[Result]) -> AgreementStats:
    if not human_results or not llm_results:
        raise ValueError("Need both human and llm results")
        
    rt = human_results[0].type
    name = human_results[0].name
    n = min(len(human_results), len(llm_results))
    
    h_vals = [r.value for r in human_results[:n]]
    l_vals = [r.value for r in llm_results[:n]]
    
    stats = AgreementStats(rubric_item_name=name, item_type=rt, n=n)
    
    if rt in ["bool", "enum"]:
        # Convert to strings for scikit-learn
        h_str = [str(x) for x in h_vals]
        l_str = [str(x) for x in l_vals]
        
        # Only compute if > 1 class exists in data to avoid warnings, though kappa handles it
        if n > 1:
            try:
                stats.kappa = float(cohen_kappa_score(h_str, l_str))
                stats.confusion_matrix = confusion_matrix(h_str, l_str).tolist()
            except Exception:
                pass
    elif rt in ["int", "float"]:
        if n > 1:
            try:
                stats.correlation = float(np.corrcoef(h_vals, l_vals)[0, 1])
            except Exception:
                pass
                
    return stats
