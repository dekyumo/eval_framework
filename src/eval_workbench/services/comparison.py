from src.eval_workbench.analysis.comparison import (
    CompareSnapshotsResult,
    compare_manifests,
    diff_summary,
    diff_to_changes,
)
from src.eval_workbench.services.agents import get_snapshot
from src.eval_workbench.services.errors import ServiceError


def compare_snapshots(repo_path: str, snapshot_a_id: str, snapshot_b_id: str) -> CompareSnapshotsResult:
    """Semantic diff between two agent snapshots."""
    snapshot_a = get_snapshot(repo_path, snapshot_a_id)
    snapshot_b = get_snapshot(repo_path, snapshot_b_id)
    if not snapshot_a:
        raise ServiceError(f"Snapshot not found: {snapshot_a_id}", 404)
    if not snapshot_b:
        raise ServiceError(f"Snapshot not found: {snapshot_b_id}", 404)

    diff = compare_manifests(snapshot_a.manifest, snapshot_b.manifest)

    return CompareSnapshotsResult(
        snapshot_a=snapshot_a_id,
        snapshot_b=snapshot_b_id,
        diff=diff,
        changes=diff_to_changes(diff, snapshot_a.manifest, snapshot_b.manifest),
        summary=diff_summary(diff),
    )
