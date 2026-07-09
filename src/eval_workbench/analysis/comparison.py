from pydantic import BaseModel
from src.eval_workbench.domain.manifest import AgentManifest
from src.eval_workbench.domain.result import AggregateResult

class SemanticDiff(BaseModel):
    added_tools: list[str]
    removed_tools: list[str]
    changed_tools: list[str]
    added_prompts: list[str]
    removed_prompts: list[str]
    changed_prompts: list[str]

def compare_manifests(m1: AgentManifest, m2: AgentManifest) -> SemanticDiff:
    t1 = {t.name: t.source_fingerprint for t in m1.tools}
    t2 = {t.name: t.source_fingerprint for t in m2.tools}
    
    added_tools = [name for name in t2 if name not in t1]
    removed_tools = [name for name in t1 if name not in t2]
    changed_tools = [name for name in t2 if name in t1 and t1[name] != t2[name]]
    
    p1 = {p.id: p.fingerprint for p in m1.prompts}
    p2 = {p.id: p.fingerprint for p in m2.prompts}
    
    added_prompts = [pid for pid in p2 if pid not in p1]
    removed_prompts = [pid for pid in p1 if pid not in p2]
    changed_prompts = [pid for pid in p2 if pid in p1 and p1[pid] != p2[pid]]
    
    return SemanticDiff(
        added_tools=added_tools,
        removed_tools=removed_tools,
        changed_tools=changed_tools,
        added_prompts=added_prompts,
        removed_prompts=removed_prompts,
        changed_prompts=changed_prompts
    )


def diff_to_changes(diff: SemanticDiff) -> list[dict]:
    changes: list[dict] = []
    for name in diff.added_tools:
        changes.append({
            "type": "added",
            "component": "Tool",
            "name": name,
            "detail": "Tool present in snapshot B but not in A",
        })
    for name in diff.removed_tools:
        changes.append({
            "type": "removed",
            "component": "Tool",
            "name": name,
            "detail": "Tool present in snapshot A but not in B",
        })
    for name in diff.changed_tools:
        changes.append({
            "type": "modified",
            "component": "Tool",
            "name": name,
            "detail": "Tool implementation fingerprint changed",
        })
    for prompt_id in diff.added_prompts:
        changes.append({
            "type": "added",
            "component": "Prompt",
            "name": prompt_id,
            "detail": "Prompt present in snapshot B but not in A",
        })
    for prompt_id in diff.removed_prompts:
        changes.append({
            "type": "removed",
            "component": "Prompt",
            "name": prompt_id,
            "detail": "Prompt present in snapshot A but not in B",
        })
    for prompt_id in diff.changed_prompts:
        changes.append({
            "type": "modified",
            "component": "Prompt",
            "name": prompt_id,
            "detail": "Prompt template fingerprint changed",
        })
    return changes


def diff_summary(diff: SemanticDiff) -> dict:
    return {
        "tools_added": len(diff.added_tools),
        "tools_removed": len(diff.removed_tools),
        "tools_modified": len(diff.changed_tools),
        "prompts_added": len(diff.added_prompts),
        "prompts_removed": len(diff.removed_prompts),
        "prompts_modified": len(diff.changed_prompts),
        "total_changes": (
            len(diff.added_tools) + len(diff.removed_tools) + len(diff.changed_tools)
            + len(diff.added_prompts) + len(diff.removed_prompts) + len(diff.changed_prompts)
        ),
    }
class RegressionDetection(BaseModel):
    metric_name: str
    old_score: float
    new_score: float
    is_regression: bool
    is_improvement: bool

def detect_regression(old_agg: AggregateResult, new_agg: AggregateResult, threshold: float = 0.05) -> RegressionDetection:
    # Example logic comparing 'proportion_true' or 'mean'
    old_val = old_agg.stats.get("proportion_true", old_agg.stats.get("mean", 0.0))
    new_val = new_agg.stats.get("proportion_true", new_agg.stats.get("mean", 0.0))
    
    diff = new_val - old_val
    return RegressionDetection(
        metric_name=old_agg.name,
        old_score=old_val,
        new_score=new_val,
        is_regression=diff < -threshold,
        is_improvement=diff > threshold
    )
