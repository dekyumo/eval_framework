"""MCP tool registry over the eval workbench HTTP API."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from src.eval_workbench.agents.case_writer.agent import GeneratedCaseDraft, GeneratedConversationTurn
from src.eval_workbench.analysis.comparison import CompareSnapshotsResult
from src.eval_workbench.analysis.response_matrix import ResponseMatrix
from src.eval_workbench.domain.blueprint import AgentBlueprint, BlueprintRunResult
from src.eval_workbench.domain.case import EvalCase, EvalDataset
from src.eval_workbench.domain.campaign import EvalCampaign
from src.eval_workbench.domain.extractor import Extractor
from src.eval_workbench.domain.governance import GovernanceProfile, GovernanceView
from src.eval_workbench.domain.gym import Gym
from src.eval_workbench.domain.rubric import Rubric
from src.eval_workbench.domain.run import EvalRun, ScoredEvalRun
from src.eval_workbench.domain.snapshot import AgentSnapshot
from src.eval_workbench.domain.tag import Tag
from src.eval_workbench.mcp.api_client import ApiClient
from src.eval_workbench.mcp.tool_defs import TOOL_NAMES, _named
from src.eval_workbench.services.errors import ServiceError

from src.eval_workbench.mcp.tool_defs import (  # noqa: F401
    PRESET_INSTRUCTIONS,
    PRESET_TOOLS,
)


def _draft_from_api(raw: dict) -> GeneratedCaseDraft:
    turns = [
        GeneratedConversationTurn(role=turn["role"], text=turn.get("text", ""))
        for turn in raw.get("conversation", [])
    ]
    return GeneratedCaseDraft(
        name=raw.get("name", ""),
        conversation=turns,
        distribution_position=raw.get("distribution_position", "in"),
        problem_type=raw.get("problem_type", "happy"),
        split=raw.get("split", "test"),
        tool_fault=raw.get("tool_fault"),
    )


def _rubric_from_api(raw: dict) -> Rubric:
    payload = dict(raw)
    for item in payload.get("items", []):
        if item.get("description") and not item.get("prompt"):
            item["prompt"] = item["description"]
    return Rubric.model_validate(payload)


def build_registry(api_url: str) -> dict[str, Callable[..., Any]]:
    """Return MCP tools that proxy to a running eval workbench HTTP API."""
    client = ApiClient(api_url)

    def list_snapshots() -> list[AgentSnapshot]:
        """List all agent snapshots stored for the target repository."""
        return [AgentSnapshot.model_validate(x) for x in client.get("/api/agents/snapshots")]

    def get_snapshot(snapshot_id: str) -> AgentSnapshot | None:
        """Fetch one snapshot by id, or None if it does not exist."""
        try:
            raw = client.get(f"/api/agents/snapshots/{snapshot_id}")
            return AgentSnapshot.model_validate(raw) if raw else None
        except ServiceError as exc:
            if exc.status_code == 404:
                return None
            raise

    def list_cases() -> list[EvalCase]:
        """List all eval cases in the registry."""
        return [EvalCase.model_validate(x) for x in client.get("/api/cases/")]

    def get_case(case_id: str) -> EvalCase | None:
        """Fetch one eval case by id, or None if it does not exist."""
        try:
            raw = client.get(f"/api/cases/{case_id}")
            return EvalCase.model_validate(raw) if raw else None
        except ServiceError as exc:
            if exc.status_code == 404:
                return None
            raise

    def list_runs() -> list[EvalRun]:
        """List all generated eval runs."""
        return [EvalRun.model_validate(x) for x in client.get("/api/runs/")]

    def list_scored_runs() -> list[ScoredEvalRun]:
        """List all scored eval runs."""
        return [ScoredEvalRun.model_validate(x) for x in client.get("/api/runs/scored")]

    def list_campaigns() -> list[EvalCampaign]:
        """List all eval campaigns."""
        return [EvalCampaign.model_validate(x) for x in client.get("/api/campaigns/")]

    def get_campaign_matrix(campaign_id: str, metric: str | None = None) -> ResponseMatrix:
        """Return the response matrix for a campaign, optionally filtered by metric."""
        params = {"metric": metric} if metric else None
        raw = client.get(f"/api/campaigns/{campaign_id}/matrix", params=params)
        return ResponseMatrix.model_validate(raw)

    def list_tags() -> list[Tag]:
        """List all registry tags."""
        return [Tag.model_validate(x) for x in client.get("/api/registries/tags")]

    def list_datasets() -> list[EvalDataset]:
        """List all eval datasets."""
        return [EvalDataset.model_validate(x) for x in client.get("/api/registries/datasets")]

    def list_rubrics() -> list[Rubric]:
        """List all scoring rubrics."""
        return [_rubric_from_api(x) for x in client.get("/api/registries/rubrics")]

    def list_extractors() -> list[Extractor]:
        """List all trace extractors."""
        return [Extractor.model_validate(x) for x in client.get("/api/registries/extractors")]

    def list_gyms() -> list[Gym]:
        """List gym environments for agentic-user simulations."""
        return [Gym.model_validate(x) for x in client.get("/api/registries/gyms")]

    def compare_snapshots(snapshot_a: str, snapshot_b: str) -> CompareSnapshotsResult:
        """Semantic diff between two agent snapshots."""
        raw = client.post(
            "/api/agents/compare",
            body={"snapshot_a": snapshot_a, "snapshot_b": snapshot_b},
        )
        return CompareSnapshotsResult.model_validate(raw)

    def get_governance(snapshot_id: str) -> GovernanceView:
        """Read the NIST AI RMF governance profile for a snapshot."""
        raw = client.get(f"/api/governance/{snapshot_id}")
        return GovernanceView.model_validate(raw)

    def scan_agent(agent_path: str, commit: str, name: str | None = None) -> AgentSnapshot:
        """Scan an ADK agent at a git commit and persist a snapshot."""
        agent_name = name or agent_path.split(":")[-1]
        raw = client.post(
            "/api/agents/scan",
            body={
                "agent_target": {"agent_path": agent_path, "name": agent_name},
                "commit": commit,
            },
        )
        return AgentSnapshot.model_validate(raw)

    def create_case(case: EvalCase, *, from_version_of: str | None = None) -> EvalCase:
        """Persist a new eval case."""
        body = case.model_dump()
        if from_version_of:
            body["from_version_of"] = from_version_of
        raw = client.post("/api/cases/", body=body)
        return EvalCase.model_validate(raw)

    def generate_case(snapshot_id: str, specification: str) -> GeneratedCaseDraft:
        """Draft an eval case from a natural-language specification."""
        raw = client.post(
            "/api/cases/generate",
            body={"snapshot_id": snapshot_id, "specification": specification},
        )
        return _draft_from_api(raw)

    def generate_run(
        snapshot_id: str,
        case_id: str,
        model_id: str,
        force: bool = False,
    ) -> EvalRun:
        """Execute one eval case against a snapshot and store the trace."""
        raw = client.post(
            "/api/runs/generate",
            body={
                "snapshot_id": snapshot_id,
                "case_id": case_id,
                "model_id": model_id,
                "force": force,
            },
        )
        return EvalRun.model_validate(raw)

    def evaluate_run(run_id: str, force: bool = False) -> ScoredEvalRun:
        """Score an existing run with its case rubrics and extractors."""
        raw = client.post(
            "/api/runs/evaluate",
            body={"run_id": run_id, "force": force},
        )
        return ScoredEvalRun.model_validate(raw)

    def create_campaign(campaign: EvalCampaign) -> EvalCampaign:
        """Create a campaign and run all dataset cases across a model panel."""
        raw = client.post("/api/campaigns/", body=campaign.model_dump())
        return EvalCampaign.model_validate(raw)

    def create_tag(tag: Tag) -> Tag:
        """Create a registry tag."""
        raw = client.post("/api/registries/tags", body=tag.model_dump())
        return Tag.model_validate(raw)

    def create_dataset(dataset: EvalDataset) -> EvalDataset:
        """Create an eval dataset."""
        raw = client.post("/api/registries/datasets", body=dataset.model_dump())
        return EvalDataset.model_validate(raw)

    def create_rubric(rubric: Rubric) -> Rubric:
        """Create a scoring rubric."""
        raw = client.post("/api/registries/rubrics", body=rubric.model_dump())
        return _rubric_from_api(raw)

    def create_extractor(extractor: Extractor, python_code: str) -> Extractor:
        """Create a trace extractor."""
        body = extractor.model_dump()
        body["python_code"] = python_code
        raw = client.post("/api/registries/extractors", body=body)
        return Extractor.model_validate(raw)

    def create_gym(gym: Gym) -> Gym:
        """Register a gym class for agentic-user eval cases."""
        raw = client.post("/api/registries/gyms", body=gym.model_dump())
        return Gym.model_validate(raw)

    def update_governance(snapshot_id: str, profile: GovernanceProfile) -> GovernanceView:
        """Update the governance profile on a snapshot."""
        raw = client.post(f"/api/governance/{snapshot_id}", body=profile.model_dump())
        return GovernanceView.model_validate(raw)

    def run_report(
        agent_path: str,
        commit: str,
        dataset_name: str,
        tags: list[str] | None = None,
        model_id: str = "gemini-2.5-flash",
        output_format: str = "markdown",
        output_path: str | None = None,
    ) -> str:
        """Run a headless benchmark report for a dataset and return the report text."""
        payload = client.post(
            "/api/benchmark/report",
            body={
                "agent_path": agent_path,
                "commit": commit,
                "dataset_name": dataset_name,
                "tags": tags,
                "model_id": model_id,
                "output_format": output_format,
                "output_path": output_path,
            },
        )
        return payload["report"]

    def run_blueprint(blueprint: AgentBlueprint) -> BlueprintRunResult:
        """Run an in-framework ADK blueprint agent to completion."""
        raw = client.post("/api/blueprints/run", body=blueprint.model_dump())
        return BlueprintRunResult.model_validate(raw)

    tools: dict[str, Callable[..., Any]] = {
        "list_snapshots": list_snapshots,
        "get_snapshot": get_snapshot,
        "list_cases": list_cases,
        "get_case": get_case,
        "list_runs": list_runs,
        "list_scored_runs": list_scored_runs,
        "list_campaigns": list_campaigns,
        "get_campaign_matrix": get_campaign_matrix,
        "list_tags": list_tags,
        "list_datasets": list_datasets,
        "list_rubrics": list_rubrics,
        "list_extractors": list_extractors,
        "list_gyms": list_gyms,
        "compare_snapshots": compare_snapshots,
        "get_governance": get_governance,
        "scan_agent": scan_agent,
        "create_case": create_case,
        "generate_case": generate_case,
        "generate_run": generate_run,
        "evaluate_run": evaluate_run,
        "create_campaign": create_campaign,
        "create_tag": create_tag,
        "create_dataset": create_dataset,
        "create_rubric": create_rubric,
        "create_extractor": create_extractor,
        "create_gym": create_gym,
        "update_governance": update_governance,
        "run_report": run_report,
        "run_blueprint": run_blueprint,
    }
    return {name: _named(name, fn) for name, fn in tools.items()}


def list_tool_names() -> list[str]:
    return list(TOOL_NAMES)
