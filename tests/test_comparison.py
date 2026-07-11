from src.eval_workbench.analysis.comparison import (
    compare_manifests,
    diff_summary,
    diff_to_changes,
)
from src.eval_workbench.domain.manifest import AgentManifest, PromptNode, ToolNode
from src.eval_workbench.domain.snapshot import AgentSnapshot, AgentTarget
from src.eval_workbench.services.comparison import compare_snapshots
from src.eval_workbench.storage.kuzu_store import close_all
from src.eval_workbench.storage.repositories import SnapshotRepository
from src.eval_workbench.storage.kuzu_store import get_connection


def _manifest(
    tools: list[ToolNode] | None = None,
    prompts: list[PromptNode] | None = None,
) -> AgentManifest:
    return AgentManifest(
        agents=[],
        tools=tools or [],
        models=[],
        prompts=prompts or [],
        root_agent_name="root",
    )


def test_compare_manifests_detects_tool_and_prompt_changes():
    m1 = _manifest(
        tools=[ToolNode(id="t1", name="search", signature="()", source_fingerprint="v1")],
        prompts=[PromptNode(id="p1", fingerprint="a", text="hello")],
    )
    m2 = _manifest(
        tools=[
            ToolNode(id="t1", name="search", signature="()", source_fingerprint="v2"),
            ToolNode(id="t2", name="calendar", signature="()", source_fingerprint="v1"),
        ],
        prompts=[PromptNode(id="p2", fingerprint="b", text="world")],
    )

    diff = compare_manifests(m1, m2)
    assert diff.added_tools == ["calendar"]
    assert diff.removed_tools == []
    assert diff.changed_tools == ["search"]
    assert diff.added_prompts == ["p2"]
    assert diff.removed_prompts == ["p1"]
    assert diff.changed_prompts == []

    changes = diff_to_changes(diff, m1, m2)
    assert len(changes) == 4
    assert {c["type"] for c in changes} == {"added", "modified", "removed"}

    prompt_removed = next(c for c in changes if c["name"] == "p1")
    assert prompt_removed["before"] == "hello"
    assert prompt_removed["after"] is None

    prompt_added = next(c for c in changes if c["name"] == "p2")
    assert prompt_added["after"] == "world"

    tool_modified = next(c for c in changes if c["name"] == "search")
    assert tool_modified["diff"]
    assert "v1" in tool_modified["before"]
    assert "v2" in tool_modified["after"]

    summary = diff_summary(diff)
    assert summary["total_changes"] == 4


def _save_snapshot(repo_path: str, snapshot_id: str, manifest: AgentManifest) -> None:
    target = AgentTarget(
        repo_path=repo_path,
        agent_path="module.agent:root",
        name="root",
    )
    snapshot = AgentSnapshot(
        id=snapshot_id,
        agent_target=target,
        commit_hash="abc123",
        timestamp=0.0,
        manifest=manifest,
        sampling_params={},
        dependency_lock="",
    )
    SnapshotRepository(get_connection(repo_path)).save(snapshot)


def test_compare_snapshots_service(tmp_path):
    repo_path = str(tmp_path)
    m1 = _manifest(
        tools=[ToolNode(id="t1", name="search", signature="()", source_fingerprint="v1")],
        prompts=[PromptNode(id="p1", fingerprint="a", text="hello")],
    )
    m2 = _manifest(
        tools=[ToolNode(id="t2", name="calendar", signature="()", source_fingerprint="v1")],
        prompts=[PromptNode(id="p1", fingerprint="b", text="hello world")],
    )
    _save_snapshot(repo_path, "snap_a", m1)
    _save_snapshot(repo_path, "snap_b", m2)

    result = compare_snapshots(repo_path, "snap_a", "snap_b")
    assert result["snapshot_a"] == "snap_a"
    assert result["summary"]["tools_added"] == 1
    assert result["summary"]["tools_removed"] == 1
    assert result["summary"]["prompts_modified"] == 1
    prompt_change = next(c for c in result["changes"] if c["component"] == "Prompt")
    assert prompt_change["diff"]
    assert "hello world" in prompt_change["after"]
    close_all()


def test_compare_snapshots_api(client, tmp_path):
    repo_path = str(tmp_path)
    m1 = _manifest()
    m2 = _manifest(prompts=[PromptNode(id="p1", fingerprint="a", text="hi")])
    _save_snapshot(repo_path, "snap_a", m1)
    _save_snapshot(repo_path, "snap_b", m2)

    client.application.config["REPO_PATH"] = repo_path
    response = client.post(
        "/api/agents/compare",
        json={"snapshot_a": "snap_a", "snapshot_b": "snap_b"},
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["summary"]["prompts_added"] == 1
    close_all()
