"""Tests for snapshot display label formatting (mirrors frontend snapshotLabel.ts)."""

from src.eval_workbench.services.snapshot_label import format_snapshot_label


def test_format_snapshot_label_short_hash_and_agent_path():
    label = format_snapshot_label({
        "id": "a44cedb4335342ebfa:src.eval_workbench.agents.case_writer.agent:root_agent",
        "commit_hash": "a44cedb4335342ebfa",
        "agent_target": {
            "agent_path": "src.eval_workbench.agents.case_writer.agent:root_agent",
        },
    })
    assert label == "a44cedb:src.eval_workbench.agents.case_writer.agent:root_agent"


def test_format_snapshot_label_fallback_from_id():
    label = format_snapshot_label({
        "id": "abcdef1234567890:module.agent:root_agent",
    })
    assert label == "abcdef1:module.agent:root_agent"
