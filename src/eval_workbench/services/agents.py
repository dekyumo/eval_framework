from __future__ import annotations

import subprocess
import traceback
from datetime import datetime

from src.eval_workbench.domain.snapshot import AgentSnapshot, AgentTarget
from src.eval_workbench.scanner.scanner import scan_agent as run_scan
from src.eval_workbench.services._conn import conn
from src.eval_workbench.services.errors import ServiceError
from src.eval_workbench.storage.repositories import SnapshotRepository


def list_snapshots(repo_path: str) -> list[dict]:
    try:
        repository = SnapshotRepository(conn(repo_path))
        snapshots = repository.get_all_snapshots()
        return [snapshot.model_dump() for snapshot in snapshots if snapshot is not None]
    except Exception as exc:
        traceback.print_exc()
        raise ServiceError(str(exc), 500) from exc


def get_snapshot(repo_path: str, snapshot_id: str) -> dict | None:
    snapshot = SnapshotRepository(conn(repo_path)).get(snapshot_id)
    if not snapshot:
        return None
    return snapshot.model_dump()


def scan(repo_path: str, agent_target: dict, commit: str) -> dict:
    target_data = dict(agent_target)
    target_data["repo_path"] = repo_path
    target = AgentTarget(**target_data)

    try:
        resolved = subprocess.run(
            ["git", "-C", target.repo_path, "rev-parse", commit],
            capture_output=True,
            text=True,
            check=True,
        )
        commit = resolved.stdout.strip()
    except subprocess.CalledProcessError as exc:
        raise ServiceError(f"Invalid commit or branch: {commit}", 400) from exc

    try:
        manifest, distribution = run_scan(target, commit)
        snapshot_id = f"{commit}:{target.agent_path}"
        snapshot = AgentSnapshot(
            id=snapshot_id,
            agent_target=target,
            commit_hash=commit,
            timestamp=datetime.now().timestamp(),
            manifest=manifest,
            distribution=distribution,
            sampling_params={},
            dependency_lock="",
        )
        SnapshotRepository(conn(target.repo_path)).save(snapshot)
        return snapshot.model_dump()
    except ServiceError:
        raise
    except Exception as exc:
        traceback.print_exc()
        raise ServiceError(str(exc), 400) from exc
