"""In-process tool registry for blueprint agents inside the eval workbench."""

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
from src.eval_workbench.domain.snapshot import AgentSnapshot, AgentTarget
from src.eval_workbench.domain.tag import Tag
from src.eval_workbench.mcp.tool_defs import TOOL_NAMES, _named
from src.eval_workbench.services import agents as agents_service
from src.eval_workbench.services import benchmark as benchmark_service
from src.eval_workbench.services import campaigns as campaigns_service
from src.eval_workbench.services import cases as cases_service
from src.eval_workbench.services import comparison as comparison_service
from src.eval_workbench.services import governance as governance_service
from src.eval_workbench.services import registries as registries_service
from src.eval_workbench.services import runs as runs_service
from src.eval_workbench.services.errors import ServiceError


def build_internal_registry(repo_path: str) -> dict[str, Callable[..., Any]]:
    """Return {tool_name: callable} bound to ``repo_path`` via the service layer."""

    def list_snapshots() -> list[AgentSnapshot]:
        return agents_service.list_snapshots(repo_path)

    def get_snapshot(snapshot_id: str) -> AgentSnapshot | None:
        return agents_service.get_snapshot(repo_path, snapshot_id)

    def list_cases() -> list[EvalCase]:
        return cases_service.list_cases(repo_path)

    def get_case(case_id: str) -> EvalCase | None:
        return cases_service.get_case(repo_path, case_id)

    def list_runs() -> list[EvalRun]:
        return runs_service.list_runs(repo_path)

    def list_scored_runs() -> list[ScoredEvalRun]:
        return runs_service.list_scored_runs(repo_path)

    def list_campaigns() -> list[EvalCampaign]:
        return campaigns_service.list_campaigns(repo_path)

    def get_campaign_matrix(campaign_id: str, metric: str | None = None) -> ResponseMatrix:
        return campaigns_service.get_matrix(repo_path, campaign_id, metric_name=metric)

    def list_tags() -> list[Tag]:
        return registries_service.list_tags(repo_path)

    def list_datasets() -> list[EvalDataset]:
        return registries_service.list_datasets(repo_path)

    def list_rubrics() -> list[Rubric]:
        return registries_service.list_rubrics(repo_path)

    def list_extractors() -> list[Extractor]:
        return registries_service.list_extractors(repo_path)

    def list_gyms() -> list[Gym]:
        return registries_service.list_gyms(repo_path)

    def compare_snapshots(snapshot_a: str, snapshot_b: str) -> CompareSnapshotsResult:
        return comparison_service.compare_snapshots(repo_path, snapshot_a, snapshot_b)

    def get_governance(snapshot_id: str) -> GovernanceView:
        return governance_service.get_governance(repo_path, snapshot_id)

    def scan_agent(agent_path: str, commit: str, name: str | None = None) -> AgentSnapshot:
        target = AgentTarget(
            repo_path=repo_path,
            agent_path=agent_path,
            name=name or agent_path.split(":")[-1],
        )
        return agents_service.scan(repo_path, target, commit)

    def create_case(case: EvalCase, *, from_version_of: str | None = None) -> EvalCase:
        return cases_service.create_case(repo_path, case, from_version_of=from_version_of)

    def generate_case(snapshot_id: str, specification: str) -> GeneratedCaseDraft:
        return cases_service.generate_case(repo_path, snapshot_id, specification)

    def generate_run(
        snapshot_id: str,
        case_id: str,
        model_id: str,
        force: bool = False,
    ) -> EvalRun:
        return runs_service.generate_run(
            repo_path,
            snapshot_id,
            case_id,
            model_id,
            force=force,
        )

    def evaluate_run(run_id: str, force: bool = False) -> ScoredEvalRun:
        return runs_service.evaluate_run(repo_path, run_id, force=force)

    def create_campaign(campaign: EvalCampaign) -> EvalCampaign:
        return campaigns_service.create_campaign(repo_path, campaign)

    def create_tag(tag: Tag) -> Tag:
        return registries_service.create_tag(repo_path, tag)

    def create_dataset(dataset: EvalDataset) -> EvalDataset:
        return registries_service.create_dataset(repo_path, dataset)

    def create_rubric(rubric: Rubric) -> Rubric:
        return registries_service.create_rubric(repo_path, rubric)

    def create_extractor(extractor: Extractor, python_code: str) -> Extractor:
        return registries_service.create_extractor(repo_path, extractor, python_code=python_code)

    def create_gym(gym: Gym) -> Gym:
        return registries_service.create_gym(repo_path, gym)

    def update_governance(snapshot_id: str, profile: GovernanceProfile) -> GovernanceView:
        return governance_service.update_governance(repo_path, snapshot_id, profile)

    def run_report(
        agent_path: str,
        commit: str,
        dataset_name: str,
        tags: list[str] | None = None,
        model_id: str = "gemini-2.5-flash",
        output_format: str = "markdown",
        output_path: str | None = None,
    ) -> str:
        return benchmark_service.run_headless_benchmark(
            repo_path,
            agent_path,
            commit,
            dataset_name,
            tags=tags,
            model_id=model_id,
            output_format=output_format,
            output_path=output_path,
        )

    def run_blueprint(blueprint: AgentBlueprint) -> BlueprintRunResult:
        from src.eval_workbench.services import blueprints as blueprints_service

        return blueprints_service.run_blueprint(repo_path, blueprint)

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


def resolve_tools(repo_path: str, names: list[str]) -> list[Callable[..., Any]]:
    """Resolve tool names to in-process callables for blueprint agents."""
    registry = build_internal_registry(repo_path)
    resolved: list[Callable[..., Any]] = []
    for name in names:
        if name not in registry:
            raise ServiceError(f"Unknown tool: {name}", 400)
        resolved.append(registry[name])
    return resolved


def list_tool_names() -> list[str]:
    return list(TOOL_NAMES)
