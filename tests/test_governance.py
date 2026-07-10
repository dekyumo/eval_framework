import pytest

from src.eval_workbench.domain.manifest import AgentManifest
from src.eval_workbench.domain.snapshot import AgentSnapshot, AgentTarget
from src.eval_workbench.services.errors import ServiceError
from src.eval_workbench.services.governance import get_governance, update_governance
from src.eval_workbench.storage.kuzu_store import close_all, get_connection
from src.eval_workbench.storage.repositories import SnapshotRepository


@pytest.fixture
def repo_path(tmp_path):
    path = str(tmp_path / "agent_repo")
    (tmp_path / "agent_repo").mkdir()
    yield path
    close_all()


def _seed_snapshot(repo_path: str) -> str:
    target = AgentTarget(
        repo_path=repo_path,
        agent_path="agent:root_agent",
        name="root",
    )
    snapshot = AgentSnapshot(
        id="snap1",
        agent_target=target,
        commit_hash="abc1234",
        timestamp=0.0,
        manifest=AgentManifest(agents=[], tools=[], models=[], prompts=[], root_agent_name="root"),
        sampling_params={},
        dependency_lock="",
    )
    SnapshotRepository(get_connection(repo_path)).save(snapshot)
    return snapshot.id


def test_get_governance_unknown_snapshot_raises(repo_path):
    with pytest.raises(ServiceError) as exc:
        get_governance(repo_path, "missing")
    assert exc.value.status_code == 404


def test_update_and_get_governance_round_trip(repo_path):
    snapshot_id = _seed_snapshot(repo_path)

    update_governance(
        repo_path,
        snapshot_id,
        {
            "concern_coverage": (
                "Concerns from Govern 1.1 (Compliance) are covered by tags 'legal' and 'compliance'"
            ),
            "business_case": "Agent costs $0.10 per run vs $1.00 for humans.",
        },
    )

    view = get_governance(repo_path, snapshot_id)
    assert "legal" in view["concern_coverage"]
    assert view["business_case"] == "Agent costs $0.10 per run vs $1.00 for humans."
    assert isinstance(view["all_tags"], list)
