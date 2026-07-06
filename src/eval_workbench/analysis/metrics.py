import numpy as np
from sklearn.metrics import (
    confusion_matrix,
    mean_absolute_percentage_error,
    precision_recall_fscore_support,
    r2_score,
)
from src.eval_workbench.domain.result import Result, AggregateResult

_FOLD_REGISTRY = {}

def register_fold(type_name: str, fn):
    _FOLD_REGISTRY[type_name] = fn

def fold_bool(results: list[Result]) -> dict:
    vals = [bool(r.value) for r in results]
    return {
        "proportion_true": sum(vals) / len(vals) if vals else 0.0,
        "average": sum(vals) / len(vals) if vals else 0.0,
        "n_true": sum(vals),
        "n_false": len(vals) - sum(vals)
    }

def fold_int(results: list[Result]) -> dict:
    vals = [int(r.value) for r in results]
    counts = {}
    for v in vals:
        counts[v] = counts.get(v, 0) + 1
    return {
        "counts": counts,
        "mean": float(np.mean(vals)) if vals else 0.0,
        "stdev": float(np.std(vals)) if len(vals) > 1 else 0.0
    }
    
def fold_float(results: list[Result]) -> dict:
    vals = [float(r.value) for r in results]
    return {
        "mean": float(np.mean(vals)) if vals else 0.0,
        "average": float(np.mean(vals)) if vals else 0.0,
        "stdev": float(np.std(vals)) if len(vals) > 1 else 0.0,
        "min": float(np.min(vals)) if vals else 0.0,
        "max": float(np.max(vals)) if vals else 0.0
    }

def fold_enum(results: list[Result]) -> dict:
    vals = [str(r.value) for r in results]
    counts = {}
    for v in vals:
        counts[v] = counts.get(v, 0) + 1
    
    mode = None
    max_c = 0
    for v, c in counts.items():
        if c > max_c:
            max_c = c
            mode = v
            
    return {
        "counts": counts,
        "mode": mode
    }

register_fold("bool", fold_bool)
register_fold("int", fold_int)
register_fold("float", fold_float)
register_fold("enum", fold_enum)


def regression_stats(y_true: list[float], y_pred: list[float]) -> dict:
    if not y_true or len(y_true) != len(y_pred):
        return {"r2": None, "mape": None, "n": 0}
    true = np.array(y_true, dtype=float)
    pred = np.array(y_pred, dtype=float)
    try:
        r2 = float(r2_score(true, pred))
    except Exception:
        r2 = None
    try:
        mape = float(mean_absolute_percentage_error(true, pred))
    except Exception:
        mape = None
    return {"r2": r2, "mape": mape, "n": len(y_true)}


def classification_stats(y_true: list[bool], y_pred: list[bool]) -> dict:
    if not y_true or len(y_true) != len(y_pred):
        return {
            "confusion_matrix": None,
            "precision": None,
            "recall": None,
            "f1": None,
            "n": 0,
        }
    true = [bool(v) for v in y_true]
    pred = [bool(v) for v in y_pred]
    labels = [False, True]
    cm = confusion_matrix(true, pred, labels=labels).tolist()
    precision, recall, f1, _ = precision_recall_fscore_support(
        true, pred, labels=labels, average="binary", zero_division=0
    )
    return {
        "confusion_matrix": cm,
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
        "n": len(y_true),
    }


def aggregate_results(name: str, results: list[Result]) -> AggregateResult:
    if not results:
        raise ValueError("Cannot aggregate empty list of results")
    
    rt = results[0].type
    if not all(r.type == rt for r in results):
        raise ValueError("All results must have the same type")
        
    fold_fn = _FOLD_REGISTRY.get(name) or _FOLD_REGISTRY.get(rt)
    if not fold_fn:
        raise ValueError(f"No fold function for type {rt}")
        
    stats = fold_fn(results)
    
    return AggregateResult(
        name=name,
        type=rt,
        n=len(results),
        stats=stats
    )
