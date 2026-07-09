from src.eval_workbench.analysis.comparison import (
    compare_manifests,
    diff_summary,
    diff_to_changes,
)
from src.eval_workbench.domain.manifest import AgentManifest
from src.eval_workbench.services.agents import get_snapshot
from src.eval_workbench.services.errors import ServiceError


def compare_snapshots(repo_path: str, snapshot_a_id: str, snapshot_b_id: str) -> dict:
    snapshot_a = get_snapshot(repo_path, snapshot_a_id)
    snapshot_b = get_snapshot(repo_path, snapshot_b_id)
    if not snapshot_a:
        raise ServiceError(f"Snapshot not found: {snapshot_a_id}", 404)
    if not snapshot_b:
        raise ServiceError(f"Snapshot not found: {snapshot_b_id}", 404)

    manifest_a = AgentManifest(**snapshot_a["manifest"])
    manifest_b = AgentManifest(**snapshot_b["manifest"])
    diff = compare_manifests(manifest_a, manifest_b)

    return {
        "snapshot_a": snapshot_a_id,
        "snapshot_b": snapshot_b_id,
        "diff": diff.model_dump(),
        "changes": diff_to_changes(diff),
        "summary": diff_summary(diff),
    }
