from unittest.mock import patch

import pytest

from src.eval_workbench.agents.case_writer.agent import GeneratedCaseDraft
from src.eval_workbench.agents.case_writer.case_writer_runner import (
    _fallback_draft,
    draft_to_dict,
    generate_eval_case,
)
from src.eval_workbench.domain.manifest import AgentManifest
from src.eval_workbench.domain.snapshot import AgentSnapshot, AgentTarget
from src.eval_workbench.services.cases import generate_case
from src.eval_workbench.services.errors import ServiceError
from src.eval_workbench.storage.kuzu_store import close_all, get_connection


def _sample_snapshot() -> AgentSnapshot:
    target = AgentTarget(
        repo_path="/tmp/repo",
        agent_path="a_single_agent.day_trip:root_agent",
        name="root",
    )
    return AgentSnapshot(
        id="snap1:a_single_agent.day_trip:root_agent",
        agent_target=target,
        commit_hash="abc123",
        timestamp=0.0,
        manifest=AgentManifest(agents=[], tools=[], models=[], prompts=[], root_agent_name="root"),
        sampling_params={},
        dependency_lock="",
    )


def test_fallback_draft_uses_specification():
    draft = _fallback_draft("Plan a weekend in Lyon")
    assert draft.conversation[0].text == "Plan a weekend in Lyon"
    assert draft.distribution_position == "in"


def test_draft_to_dict_maps_conversation():
    snapshot = _sample_snapshot()
    draft = GeneratedCaseDraft(
        name="Lyon weekend",
        conversation=[{"role": "user", "text": "Plan a weekend in Lyon"}],
        distribution_position="margin",
        problem_type="happy",
    )
    result = draft_to_dict(draft)
    assert result["name"] == "Lyon weekend"
    assert result["conversation"][0]["text"] == "Plan a weekend in Lyon"
    assert result["distribution_position"] == "margin"
    assert result["source"] == "generated"


def test_generate_eval_case_uses_fallback_on_agent_failure():
    snapshot = _sample_snapshot()
    with patch(
        "src.eval_workbench.agents.case_writer.case_writer_runner._run_case_writer_async",
        side_effect=RuntimeError("agent unavailable"),
    ):
        result = generate_eval_case(snapshot, "Plan a day in Paris with $500")
    assert result["conversation"][0]["text"] == "Plan a day in Paris with $500"
    assert result["name"] == "Generated case"


def test_generate_case_service_validates_input(tmp_path):
    repo_path = str(tmp_path / "agent_repo")
    with pytest.raises(ServiceError) as exc:
        generate_case(repo_path, "", "spec")
    assert exc.value.status_code == 400

    with pytest.raises(ServiceError) as exc:
        generate_case(repo_path, "missing", "spec")
    assert exc.value.status_code == 404


def test_generate_case_service_with_snapshot(tmp_path):
    repo_path = str(tmp_path / "agent_repo")
    snapshot = _sample_snapshot()
    snapshot.agent_target.repo_path = repo_path

    try:
        conn = get_connection(repo_path)
        from src.eval_workbench.storage.repositories import SnapshotRepository

        SnapshotRepository(conn).save(snapshot)

        with patch(
            "src.eval_workbench.services.cases.generate_eval_case",
            return_value={
                "name": "Paris trip",
                "conversation": [{"role": "user", "kind": "text", "text": "Paris $500"}],
                "distribution_position": "in",
                "problem_type": "happy",
                "split": "test",
                "tool_fault": None,
                "metrics": [],
                "tags": [],
                "source": "generated",
            },
        ):
            result = generate_case(repo_path, snapshot.id, "Plan Paris")
        assert result["name"] == "Paris trip"
        assert result["conversation"][0]["text"] == "Paris $500"
    finally:
        close_all()
