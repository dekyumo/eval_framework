"""Service function tools for chat operator."""

from eval_workbench.services import agents, cases, comparison, runs, tags
from eval_workbench.services.proposals import ActionProposal


def list_snapshots(agent_path: str | None = None) -> list:
    return [s.model_dump() for s in agents.list_snapshots(agent_path)]


def get_snapshot(snapshot_id: str) -> dict | None:
    s = agents.get_snapshot(snapshot_id)
    return s.model_dump() if s else None


def list_cases(tags: list[str] | None = None) -> list:
    return [c.model_dump() for c in cases.list_cases(tags)]


def compare_snapshots(a: str, b: str) -> dict:
    return comparison.compare_snapshots(a, b)


def propose_scan(agent_path: str, commit: str = "HEAD") -> ActionProposal:
    return ActionProposal(
        action="scan_snapshot",
        params={"agent_path": agent_path, "commit": commit},
        summary=f"Scan {agent_path} at {commit}",
    )


def confirm_scan(proposal: ActionProposal) -> dict:
    snap = agents.scan_snapshot(
        proposal.params["agent_path"],
        proposal.params.get("commit", "HEAD"),
    )
    return snap.model_dump()
