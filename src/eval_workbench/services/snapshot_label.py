"""Human-readable snapshot labels for UI and APIs."""

from __future__ import annotations

from typing import Any


def short_commit_hash(commit_hash: str, length: int = 7):
    if not commit_hash:
        return ""
    return commit_hash[:length] if len(commit_hash) > length else commit_hash


def format_snapshot_label(snapshot: dict[str, Any]):
    """Format as short_hash:module.path:agent_var."""
    agent_target = snapshot.get("agent_target") or {}
    agent_path = agent_target.get("agent_path")
    commit = snapshot.get("commit_hash") or snapshot.get("id", "").split(":", 1)[0]
    short_hash = short_commit_hash(commit)

    if agent_path:
        return f"{short_hash}:{agent_path}"

    snapshot_id = snapshot.get("id", "")
    if ":" in snapshot_id:
        id_commit, rest = snapshot_id.split(":", 1)
        return f"{short_commit_hash(id_commit)}:{rest}"

    return snapshot_id
