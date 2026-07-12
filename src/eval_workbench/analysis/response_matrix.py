import numpy as np
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.cluster import KMeans
from src.eval_workbench.domain.result import Result
from pydantic import BaseModel

class ResponseMatrix(BaseModel):
    campaign_id: str
    models: list[str]
    case_ids: list[str]
    cell: dict[str, float]
    metric_name: str = ""
    metric_type: str = "bool"
    available_metrics: list[dict[str, str]] = []
    # derivations
    difficulty: dict[str, float] = {}
    ability: dict[str, float] = {}
    clusters: dict[str, int] = {}
    redundant_pairs: list[tuple[str, str]] = []

def build_response_matrix(campaign_id: str, results: list[Result], models: list[str], case_ids: list[str]) -> ResponseMatrix:
    cell = {}
    # Assume results list has enough information to map to (model, case)
    # We will just map linearly for the mock if we don't have true mapping, 
    # but in a real campaign the results belong to runs that identify the model and case.
    
    # We will simulate data for now if results are empty, otherwise use results.
    # In practice, cell[f"{m}|{c}"] is the float or boolean (0.0/1.0) value.
    if not results:
        for m in models:
            for c in case_ids:
                cell[f"{m}|{c}"] = np.random.choice([0.0, 1.0])
        is_float = False
    else:
        # Build cell from results if possible. Assuming results have some identifier, but Result doesn't.
        # So the service should pass the cell dictionary instead. But keeping signature for now.
        for m in models:
            for c in case_ids:
                cell[f"{m}|{c}"] = 0.5
        is_float = any(r.type == "float" for r in results)

    X = []
    y = []
    for m_idx, m in enumerate(models):
        for c_idx, c in enumerate(case_ids):
            features = [0] * (len(models) + len(case_ids))
            features[m_idx] = 1
            features[len(models) + c_idx] = 1
            X.append(features)
            y.append(cell[f"{m}|{c}"])
            
    difficulty = {}
    ability = {}
    clusters = {}
    
    if len(set(y)) > 1:
        if is_float:
            # Simple Linear Regression
            clf = LinearRegression(fit_intercept=False)
            clf.fit(X, y)
            coefs = clf.coef_
            for m_idx, m in enumerate(models):
                ability[m] = float(coefs[m_idx])
            for c_idx, c in enumerate(case_ids):
                difficulty[c] = float(-coefs[len(models) + c_idx])
        else:
            # Logistic Regression for IRT
            clf = LogisticRegression(fit_intercept=False, penalty=None)
            clf.fit(X, y)
            coefs = clf.coef_[0]
            for m_idx, m in enumerate(models):
                ability[m] = float(coefs[m_idx])
            for c_idx, c in enumerate(case_ids):
                difficulty[c] = float(-coefs[len(models) + c_idx])
            
        case_vectors = []
        for c in case_ids:
            vec = [cell[f"{m}|{c}"] for m in models]
            case_vectors.append(vec)
            
        if len(case_ids) >= 2:
            n_clusters = min(3, len(case_ids))
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            cluster_labels = kmeans.fit_predict(case_vectors)
            for c_idx, c in enumerate(case_ids):
                clusters[c] = int(cluster_labels[c_idx])
                
    return ResponseMatrix(
        campaign_id=campaign_id,
        models=models,
        case_ids=case_ids,
        cell=cell,
        difficulty=difficulty,
        ability=ability,
        clusters=clusters,
        redundant_pairs=[]
    )
