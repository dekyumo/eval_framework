"""Headless benchmark runner for CI/CD pipelines."""

from __future__ import annotations

import json
from dataclasses import dataclass, field

from src.eval_workbench.analysis.metrics import (
    aggregate_results,
    classification_stats,
    regression_stats,
)
from src.eval_workbench.domain.case import EvalCase, EvalDataset
from src.eval_workbench.domain.result import Result
from src.eval_workbench.domain.tag import Tag
from src.eval_workbench.extraction.extractor import run_extractor
from src.eval_workbench.services import agents as agents_service
from src.eval_workbench.services import runs as runs_service
from src.eval_workbench.services._conn import conn
from src.eval_workbench.services.errors import ServiceError
from src.eval_workbench.storage.repositories import (
    EvalCaseRepository,
    EvalDatasetRepository,
    ExtractorRepository,
    TagRepository,
)


@dataclass
class CaseRunOutcome:
    case: EvalCase
    run_id: str | None = None
    skipped: bool = False
    skip_reason: str | None = None
    results: list[Result] = field(default_factory=list)


def _tag_aliases(connection, tag_filters: list[str]) -> set[str]:
    if not tag_filters:
        return set()
    tags = TagRepository(connection).get_all("Tag", "id", Tag)
    aliases: set[str] = set()
    for requested in tag_filters:
        aliases.add(requested)
        for tag in tags:
            if tag.id == requested or tag.name == requested:
                aliases.add(tag.id)
                aliases.add(tag.name)
    return aliases


def _case_matches_tags(case: EvalCase, tag_aliases: set[str]) -> bool:
    if not tag_aliases:
        return True
    return bool(set(case.tags or []) & tag_aliases)


def _dataset_by_name(connection, dataset_name: str) -> EvalDataset:
    datasets = EvalDatasetRepository(connection).get_all("EvalDataset", "id", EvalDataset)
    for dataset in datasets:
        if dataset.name == dataset_name or dataset.id == dataset_name:
            return dataset
    raise ServiceError(f"Dataset not found: {dataset_name}", 404)


def select_cases(
    connection,
    dataset_name: str,
    tag_filters: list[str] | None = None,
) -> list[EvalCase]:
    dataset = _dataset_by_name(connection, dataset_name)
    aliases = _tag_aliases(connection, tag_filters or [])
    unique_case_ids = list(dict.fromkeys(dataset.case_ids or []))

    cases: list[EvalCase] = []
    repository = EvalCaseRepository(connection)
    for case_id in unique_case_ids:
        case = repository.get(case_id)
        if case and _case_matches_tags(case, aliases):
            cases.append(case)
    return cases


def _coerce_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _coerce_float(value) -> float:
    text = str(value).strip().replace("$", "").replace(",", "")
    return float(text)


def _extractor_pairs(
    case: EvalCase,
    trace,
    connection,
) -> list[tuple[str, str, object, object]]:
    pairs: list[tuple[str, str, object, object]] = []
    for metric in case.metrics:
        if metric.strategy != "deterministic" or not metric.extractor_ref:
            continue
        extractor = ExtractorRepository(connection).get(metric.extractor_ref)
        if not extractor:
            continue
        try:
            predicted = run_extractor(extractor, trace)
        except Exception:
            continue
        if metric.ground_truth is None or str(metric.ground_truth).strip() == "":
            continue
        pairs.append((metric.name, metric.extractor_ref, metric.ground_truth, predicted))
    return pairs


def render_markdown_report(
    snapshot: dict,
    outcomes: list[CaseRunOutcome],
    rubric_aggregates: dict[str, dict],
    extractor_aggregates: dict[str, dict],
) -> str:
    lines: list[str] = [
        "# Eval Benchmark Report",
        "",
        "## Agent Snapshot",
        "",
        "```json",
        json.dumps(snapshot, indent=2),
        "```",
        "",
        "## Per-case Results",
        "",
        "| Case | Metric | Type | Value | Source |",
        "| --- | --- | --- | --- | --- |",
    ]

    for outcome in outcomes:
        case_label = outcome.case.name or outcome.case.id
        if outcome.skipped:
            lines.append(f"| {case_label} | _skipped_ | | {outcome.skip_reason or 'error'} | |")
            continue
        for result in outcome.results:
            lines.append(
                f"| {case_label} | {result.name} | {result.type} | {result.value} | {result.source} |"
            )

    lines.extend(["", "## Rubric Summary", ""])
    if rubric_aggregates:
        lines.append("| Rubric Item | Type | Average | TRUE | FALSE | N |")
        lines.append("| --- | --- | --- | --- | --- | --- |")
        for name, stats in sorted(rubric_aggregates.items()):
            if stats["type"] == "bool":
                lines.append(
                    f"| {name} | bool | {stats.get('average', 0):.3f} | "
                    f"{stats.get('n_true', 0)} | {stats.get('n_false', 0)} | {stats.get('n', 0)} |"
                )
            else:
                lines.append(
                    f"| {name} | {stats['type']} | {stats.get('average', 0):.3f} | | | {stats.get('n', 0)} |"
                )
    else:
        lines.append("_No rubric metrics were scored._")

    lines.extend(["", "## Extractor Summary", ""])
    if extractor_aggregates:
        for name, stats in sorted(extractor_aggregates.items()):
            lines.append(f"### {name}")
            if stats["kind"] == "bool":
                lines.append(f"- Precision: {stats.get('precision')}")
                lines.append(f"- Recall: {stats.get('recall')}")
                lines.append(f"- F1: {stats.get('f1')}")
                lines.append(f"- Confusion matrix: `{stats.get('confusion_matrix')}`")
            else:
                lines.append(f"- R2: {stats.get('r2')}")
                lines.append(f"- MAPE: {stats.get('mape')}")
            lines.append(f"- N: {stats.get('n', 0)}")
            lines.append("")
    else:
        lines.append("_No deterministic extractor metrics with ground truth were scored._")

    return "\n".join(lines)


def run_headless_benchmark(
    repo_path: str,
    agent_path: str,
    commit: str,
    dataset_name: str,
    tags: list[str] | None = None,
    model_id: str = "gemini-2.5-flash",
) -> str:
    agent_name = agent_path.split(":")[-1]
    snapshot = agents_service.scan(
        repo_path,
        {"agent_path": agent_path, "name": agent_name},
        commit,
    )
    snapshot_id = snapshot["id"]
    connection = conn(repo_path)
    cases = select_cases(connection, dataset_name, tags)
    if not cases:
        raise ServiceError("No matching cases found for dataset/tags filter", 404)

    outcomes: list[CaseRunOutcome] = []
    rubric_results: dict[str, list[Result]] = {}
    extractor_values: dict[str, dict[str, list]] = {}

    for case in cases:
        run_data = runs_service.generate_run(repo_path, snapshot_id, case.id, model_id)
        trace = run_data["trace"]
        if trace.get("exception"):
            outcomes.append(
                CaseRunOutcome(
                    case=case,
                    run_id=run_data.get("id"),
                    skipped=True,
                    skip_reason="trace exception",
                )
            )
            continue

        scored = runs_service.evaluate_run(repo_path, run_data["id"])
        results = [Result.model_validate(item) for item in scored.get("results", [])]
        outcomes.append(CaseRunOutcome(case=case, run_id=run_data["id"], results=results))

        for result in results:
            if result.source == "llm_judge":
                rubric_results.setdefault(result.name, []).append(result)

        from src.eval_workbench.domain.trace import Trace

        trace_obj = Trace.model_validate(trace)
        for metric_name, extractor_ref, ground_truth, predicted in _extractor_pairs(
            case, trace_obj, connection
        ):
            bucket = extractor_values.setdefault(
                metric_name,
                {"extractor_ref": extractor_ref, "result_type": None, "y_true": [], "y_pred": []},
            )
            metric_def = next(m for m in case.metrics if m.name == metric_name)
            bucket["result_type"] = metric_def.result_type
            if metric_def.result_type == "bool":
                bucket["y_true"].append(_coerce_bool(ground_truth))
                bucket["y_pred"].append(_coerce_bool(predicted))
            elif metric_def.result_type in {"int", "float"}:
                bucket["y_true"].append(_coerce_float(ground_truth))
                bucket["y_pred"].append(_coerce_float(predicted))

    rubric_aggregates: dict[str, dict] = {}
    for name, results in rubric_results.items():
        agg = aggregate_results(name, results)
        rubric_aggregates[name] = {"type": agg.type, "n": agg.n, **agg.stats}

    extractor_aggregates: dict[str, dict] = {}
    for name, bucket in extractor_values.items():
        y_true = bucket["y_true"]
        y_pred = bucket["y_pred"]
        if bucket["result_type"] == "bool":
            stats = classification_stats(y_true, y_pred)
            stats["kind"] = "bool"
            extractor_aggregates[name] = stats
        elif bucket["result_type"] in {"int", "float"}:
            stats = regression_stats(y_true, y_pred)
            stats["kind"] = "float"
            extractor_aggregates[name] = stats

    return render_markdown_report(snapshot, outcomes, rubric_aggregates, extractor_aggregates)
