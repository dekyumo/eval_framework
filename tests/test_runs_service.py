from unittest.mock import patch

import pytest

from src.eval_workbench.domain.case import EvalCase
from src.eval_workbench.domain.manifest import AgentManifest
from src.eval_workbench.domain.snapshot import AgentSnapshot, AgentTarget
from src.eval_workbench.domain.run import EvalRun
from src.eval_workbench.domain.trace import MessagePart, Trace, TokenUsage
from src.eval_workbench.services.runs import find_existing_run, generate_run
from src.eval_workbench.storage.kuzu_store import close_all, get_connection
from src.eval_workbench.storage.repositories import EvalCaseRepository, EvalRunRepository, SnapshotRepository


@pytest.fixture
def repo_path(tmp_path):
    path = str(tmp_path / "agent_repo")
    (tmp_path / "agent_repo").mkdir()
    yield path
    close_all()


def _seed_snapshot_and_case(repo_path: str) -> tuple[str, str]:
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
    case = EvalCase(
        id="case1",
        name="Paris trip",
        target_agent_path="agent:root_agent",
        conversation=[MessagePart(role="user", kind="text", text="hi")],
        distribution_position="in",
        problem_type="happy",
    )
    connection = get_connection(repo_path)
    SnapshotRepository(connection).save(snapshot)
    EvalCaseRepository(connection).save(case)
    return snapshot.id, case.id


def test_generate_run_skips_when_run_already_exists(repo_path):
    snapshot_id, case_id = _seed_snapshot_and_case(repo_path)
    trace = Trace(
        id="trace_old",
        parts=[],
        snapshot_id=snapshot_id,
        case_id=case_id,
        model_id="gemini-2.5-flash",
        latency_ms=1.0,
        tokens=TokenUsage(),
    )

    with patch("src.eval_workbench.services.runs.AgentRunner") as runner_cls:
        runner_cls.return_value.run_case.return_value = trace
        first = generate_run(repo_path, snapshot_id, case_id, "gemini-2.5-flash")
        second = generate_run(repo_path, snapshot_id, case_id, "gemini-2.5-flash")

    assert first["id"] == second["id"]
    assert runner_cls.return_value.run_case.call_count == 1

    connection = get_connection(repo_path)
    all_runs = EvalRunRepository(connection).get_all("EvalRun", "id", EvalRun)
    assert len(all_runs) == 1


def test_generate_run_force_reruns_and_upserts(repo_path):
    snapshot_id, case_id = _seed_snapshot_and_case(repo_path)
    trace_v1 = Trace(
        id="trace_v1",
        parts=[MessagePart(role="user", kind="text", text="first")],
        snapshot_id=snapshot_id,
        case_id=case_id,
        model_id="gemini-2.5-flash",
        latency_ms=10.0,
        tokens=TokenUsage(),
    )
    trace_v2 = Trace(
        id="trace_v2",
        parts=[MessagePart(role="user", kind="text", text="second")],
        snapshot_id=snapshot_id,
        case_id=case_id,
        model_id="gemini-2.5-flash",
        latency_ms=20.0,
        tokens=TokenUsage(),
    )

    with patch("src.eval_workbench.services.runs.AgentRunner") as runner_cls:
        runner_cls.return_value.run_case.side_effect = [trace_v1, trace_v2]
        first = generate_run(repo_path, snapshot_id, case_id, "gemini-2.5-flash")
        second = generate_run(
            repo_path, snapshot_id, case_id, "gemini-2.5-flash", force=True
        )

    assert first["id"] == second["id"]
    assert second["trace"]["latency_ms"] == 20.0
    assert runner_cls.return_value.run_case.call_count == 2

    connection = get_connection(repo_path)
    all_runs = EvalRunRepository(connection).get_all("EvalRun", "id", EvalRun)
    assert len(all_runs) == 1
    assert find_existing_run(connection, snapshot_id, case_id, "gemini-2.5-flash") is not None
