"""Shared tool registry.

The registry wraps the service layer as plain, name-addressable callables. Both
the stdio MCP server and the in-framework blueprint runner resolve tools through
here, so the "tools by name" contract is identical inside and outside the
framework.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

from src.eval_workbench.analysis.comparison import SemanticDiff, compare_manifests
from src.eval_workbench.domain.blueprint import BlueprintPreset
from src.eval_workbench.domain.manifest import AgentManifest
from src.eval_workbench.services import agents as agents_service
from src.eval_workbench.services import benchmark as benchmark_service
from src.eval_workbench.services import campaigns as campaigns_service
from src.eval_workbench.services import cases as cases_service
from src.eval_workbench.services import governance as governance_service
from src.eval_workbench.services import registries as registries_service
from src.eval_workbench.services import runs as runs_service
from src.eval_workbench.services.errors import ServiceError

TOOL_NAMES: list[str] = [
    # read
    "list_snapshots",
    "get_snapshot",
    "list_cases",
    "get_case",
    "list_runs",
    "list_scored_runs",
    "list_campaigns",
    "get_campaign_matrix",
    "list_tags",
    "list_datasets",
    "list_rubrics",
    "list_extractors",
    "compare_snapshots",
    "get_governance",
    # write / expensive
    "scan_agent",
    "create_case",
    "generate_case",
    "generate_run",
    "evaluate_run",
    "create_campaign",
    "create_tag",
    "create_dataset",
    "create_rubric",
    "create_extractor",
    "update_governance",
    "run_report",
    "run_blueprint",
]

PRESET_TOOLS: dict[BlueprintPreset, list[str]] = {
    BlueprintPreset.scanner: ["scan_agent", "get_snapshot", "list_snapshots"],
    BlueprintPreset.registry_explorer: [
        "list_tags",
        "list_datasets",
        "list_rubrics",
        "list_extractors",
    ],
    BlueprintPreset.registry_updater: [
        "create_tag",
        "create_dataset",
        "create_rubric",
        "create_extractor",
        "list_tags",
        "list_datasets",
        "list_rubrics",
        "list_extractors",
    ],
    BlueprintPreset.case_maker: [
        "generate_case",
        "create_case",
        "list_cases",
        "get_snapshot",
        "list_tags",
    ],
    BlueprintPreset.case_runner: [
        "generate_run",
        "list_runs",
        "get_case",
        "list_snapshots",
    ],
    BlueprintPreset.case_eval_runner: [
        "evaluate_run",
        "list_scored_runs",
        "list_runs",
    ],
    BlueprintPreset.campaign_runner: [
        "create_campaign",
        "get_campaign_matrix",
        "list_campaigns",
        "list_datasets",
    ],
    BlueprintPreset.data_writer: [
        "run_report",
        "get_snapshot",
        "list_scored_runs",
    ],
}

PRESET_INSTRUCTIONS: dict[BlueprintPreset, str] = {
    BlueprintPreset.scanner: (
        "You are a Scanner agent. Scan an agent at a given commit and confirm the "
        "snapshot is stored. Do scan_agent, get_snapshot, and list_snapshots until "
        "the new snapshot exists and looks correct. "
        "Example: scan_agent → get_snapshot → list_snapshots."
    ),
    BlueprintPreset.registry_explorer: (
        "You are a RegistryExplorer. Inventory tags, datasets, rubrics, and "
        "extractors. Call list_tags, list_datasets, list_rubrics, and list_extractors "
        "until you have a complete picture of registry objects. "
        "Example: list_tags → list_datasets → list_rubrics → list_extractors."
    ),
    BlueprintPreset.registry_updater: (
        "You are a RegistryUpdater. Create or verify registry objects (tags, datasets, "
        "rubrics, extractors). Use create_* tools, then list_* tools to confirm. "
        "Repeat until requested registry entries exist. "
        "Example: create_tag → list_tags → create_dataset → list_datasets."
    ),
    BlueprintPreset.case_maker: (
        "You are a CaseMaker. Draft and persist eval cases for a snapshot. Use "
        "generate_case and create_case, then list_cases and get_snapshot to verify. "
        "Repeat until the case set matches the specification. "
        "Example: get_snapshot → generate_case → create_case → list_cases."
    ),
    BlueprintPreset.case_runner: (
        "You are a CaseRunner. Execute eval cases against snapshots. Use generate_run "
        "and list_runs, consulting get_case and list_snapshots as needed, until runs "
        "exist for the target cases. "
        "Example: get_case → generate_run → list_runs."
    ),
    BlueprintPreset.case_eval_runner: (
        "You are a CaseEvalRunner. Score existing runs. Call evaluate_run, then "
        "list_scored_runs and list_runs until every target run is scored. "
        "Example: list_runs → evaluate_run → list_scored_runs."
    ),
    BlueprintPreset.campaign_runner: (
        "You are a CampaignRunner. Create campaigns and inspect their matrices. Use "
        "create_campaign, get_campaign_matrix, list_campaigns, and list_datasets until "
        "the campaign is created and results are available. "
        "Example: list_datasets → create_campaign → get_campaign_matrix."
    ),
    BlueprintPreset.data_writer: (
        "You are a DataWriter. Produce evaluation reports and cross-check snapshot "
        "data. Use run_report, get_snapshot, and list_scored_runs until the report "
        "is written and scored runs are accounted for. "
        "Example: list_scored_runs → run_report → get_snapshot."
    ),
}


def _summarize_diff(diff: SemanticDiff) -> str:
    parts: list[str] = []
    if diff.added_tools:
        parts.append(f"added tools: {', '.join(diff.added_tools)}")
    if diff.removed_tools:
        parts.append(f"removed tools: {', '.join(diff.removed_tools)}")
    if diff.changed_tools:
        parts.append(f"changed tools: {', '.join(diff.changed_tools)}")
    if diff.added_prompts:
        parts.append(f"added prompts: {', '.join(diff.added_prompts)}")
    if diff.removed_prompts:
        parts.append(f"removed prompts: {', '.join(diff.removed_prompts)}")
    if diff.changed_prompts:
        parts.append(f"changed prompts: {', '.join(diff.changed_prompts)}")
    return "; ".join(parts) if parts else "No manifest changes detected"


def _named(name: str, fn: Callable[..., Any]) -> Callable[..., Any]:
    fn.__name__ = name
    if not fn.__doc__:
        fn.__doc__ = f"Eval workbench tool: {name}"
    return fn


def build_registry(repo_path: str) -> dict[str, Callable[..., Any]]:
    """Return {tool_name: callable} with `repo_path` bound where the underlying
    service requires it. Callables take plain JSON-serialisable args/returns so
    they work as both ADK FunctionTools and MCP tools.
    """

    def list_snapshots() -> list[dict]:
        return agents_service.list_snapshots(repo_path)

    def get_snapshot(snapshot_id: str) -> dict | None:
        return agents_service.get_snapshot(repo_path, snapshot_id)

    def list_cases() -> list[dict]:
        return cases_service.list_cases(repo_path)

    def get_case(case_id: str) -> dict | None:
        return cases_service.get_case(repo_path, case_id)

    def list_runs() -> list[dict]:
        return runs_service.list_runs(repo_path)

    def list_scored_runs() -> list[dict]:
        return runs_service.list_scored_runs(repo_path)

    def list_campaigns() -> list[dict]:
        return campaigns_service.list_campaigns(repo_path)

    def get_campaign_matrix(campaign_id: str) -> dict:
        return campaigns_service.get_matrix(repo_path, campaign_id)

    def list_tags() -> list[dict]:
        return registries_service.list_tags(repo_path)

    def list_datasets() -> list[dict]:
        return registries_service.list_datasets(repo_path)

    def list_rubrics() -> list[dict]:
        return registries_service.list_rubrics(repo_path)

    def list_extractors() -> list[dict]:
        return registries_service.list_extractors(repo_path)

    def compare_snapshots(snapshot_a: str, snapshot_b: str) -> dict:
        left = agents_service.get_snapshot(repo_path, snapshot_a)
        right = agents_service.get_snapshot(repo_path, snapshot_b)
        if not left or not right:
            raise ServiceError("Snapshot not found", 404)

        manifest_a = AgentManifest.model_validate(left.get("manifest") or {})
        manifest_b = AgentManifest.model_validate(right.get("manifest") or {})
        diff = compare_manifests(manifest_a, manifest_b)
        changes = {
            "tools": {
                "added": diff.added_tools,
                "removed": diff.removed_tools,
                "changed": diff.changed_tools,
            },
            "prompts": {
                "added": diff.added_prompts,
                "removed": diff.removed_prompts,
                "changed": diff.changed_prompts,
            },
        }
        return {
            "diff": diff.model_dump(),
            "changes": changes,
            "summary": _summarize_diff(diff),
        }

    def get_governance(snapshot_id: str) -> dict:
        return governance_service.get_governance(repo_path, snapshot_id)

    def scan_agent(agent_path: str, commit: str, name: str | None = None) -> dict:
        agent_name = name or agent_path.split(":")[-1]
        return agents_service.scan(
            repo_path,
            {"agent_path": agent_path, "name": agent_name},
            commit,
        )

    def create_case(data: dict, dataset_id: str | None = None) -> dict:
        return cases_service.create_case(repo_path, data, dataset_id=dataset_id)

    def generate_case(snapshot_id: str, specification: str) -> dict:
        return cases_service.generate_case(repo_path, snapshot_id, specification)

    def generate_run(
        snapshot_id: str,
        case_id: str,
        model_id: str,
        force: bool = False,
    ) -> dict:
        return runs_service.generate_run(
            repo_path,
            snapshot_id,
            case_id,
            model_id,
            force=force,
        )

    def evaluate_run(run_id: str) -> dict:
        return runs_service.evaluate_run(repo_path, run_id)

    def create_campaign(data: dict) -> dict:
        return campaigns_service.create_campaign(repo_path, data)

    def create_tag(data: dict) -> dict:
        return registries_service.create_tag(repo_path, data)

    def create_dataset(data: dict) -> dict:
        return registries_service.create_dataset(repo_path, data)

    def create_rubric(data: dict) -> dict:
        return registries_service.create_rubric(repo_path, data)

    def create_extractor(data: dict) -> dict:
        return registries_service.create_extractor(repo_path, data)

    def update_governance(snapshot_id: str, data: dict) -> dict:
        return governance_service.update_governance(repo_path, snapshot_id, data)

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

    def run_blueprint(blueprint: dict) -> dict:
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
        "update_governance": update_governance,
        "run_report": run_report,
        "run_blueprint": run_blueprint,
    }
    return {name: _named(name, fn) for name, fn in tools.items()}


def resolve_tools(repo_path: str, names: list[str]) -> list[Callable[..., Any]]:
    """Resolve tool names to callables. Raises ServiceError(400) on unknown name."""
    registry = build_registry(repo_path)
    resolved: list[Callable[..., Any]] = []
    for name in names:
        if name not in registry:
            raise ServiceError(f"Unknown tool: {name}", 400)
        resolved.append(registry[name])
    return resolved


def list_tool_names() -> list[str]:
    return list(TOOL_NAMES)
