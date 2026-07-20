"""Shared MCP tool names, blueprint presets, and naming helpers."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from src.eval_workbench.domain.blueprint import BlueprintPreset

TOOL_NAMES: list[str] = [
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
    "list_gyms",
    "compare_snapshots",
    "get_governance",
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
    "create_gym",
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
        "list_gyms",
    ],
    BlueprintPreset.registry_updater: [
        "create_tag",
        "create_dataset",
        "create_rubric",
        "create_extractor",
        "create_gym",
        "list_tags",
        "list_datasets",
        "list_rubrics",
        "list_extractors",
        "list_gyms",
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
        "You are a RegistryExplorer. Inventory tags, datasets, rubrics, extractors, "
        "and gyms. Call list_tags, list_datasets, list_rubrics, list_extractors, and "
        "list_gyms until you have a complete picture of registry objects. "
        "Example: list_tags → list_datasets → list_rubrics → list_extractors → list_gyms."
    ),
    BlueprintPreset.registry_updater: (
        "You are a RegistryUpdater. Create or verify registry objects (tags, datasets, "
        "rubrics, extractors, gyms). Use create_* tools, then list_* tools to confirm. "
        "Repeat until requested registry entries exist. "
        "Example: create_gym → list_gyms → create_dataset → list_datasets."
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


def _named(name: str, fn: Callable[..., Any]) -> Callable[..., Any]:
    fn.__name__ = name
    if not fn.__doc__:
        fn.__doc__ = f"Eval workbench tool: {name}"
    return fn
