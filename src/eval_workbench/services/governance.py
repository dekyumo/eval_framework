"""Governance / NIST-alignment service.

Reads and persists the `GovernanceProfile` on an `AgentSnapshot`. Persistence
reuses `SnapshotRepository` (no separate store); see
issues/rescan_persistence_two_scan_modes.md.
"""

from __future__ import annotations

from src.eval_workbench.domain.governance import GovernanceProfile, GovernanceView, TagSummary
from src.eval_workbench.domain.tag import Tag
from src.eval_workbench.services._conn import conn
from src.eval_workbench.services.errors import ServiceError
from src.eval_workbench.storage.repositories import SnapshotRepository, TagRepository


def get_governance(repo_path: str, snapshot_id: str) -> GovernanceView:
    """Read the NIST AI RMF governance profile for a snapshot."""
    connection = conn(repo_path)
    snapshot = SnapshotRepository(connection).get(snapshot_id)
    if not snapshot:
        raise ServiceError(f"Snapshot not found: {snapshot_id}", 404)

    profile = snapshot.governance
    tags = TagRepository(connection).get_all("Tag", "id", Tag)

    return GovernanceView(
        snapshot_id=snapshot_id,
        concern_coverage=profile.concern_coverage if profile else "",
        business_case=profile.business_case if profile else "",
        all_tags=[TagSummary(id=tag.id, name=tag.name) for tag in tags],
    )


def update_governance(repo_path: str, snapshot_id: str, profile: GovernanceProfile) -> GovernanceView:
    """Update the governance profile on a snapshot."""
    connection = conn(repo_path)
    repository = SnapshotRepository(connection)
    snapshot = repository.get(snapshot_id)
    if not snapshot:
        raise ServiceError(f"Snapshot not found: {snapshot_id}", 404)

    snapshot.governance = profile
    repository.save(snapshot)
    return get_governance(repo_path, snapshot_id)
