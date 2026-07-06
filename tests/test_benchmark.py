from unittest.mock import patch

import pytest

from src.eval_workbench.analysis.metrics import classification_stats, regression_stats
from src.eval_workbench.domain.case import EvalCase, EvalDataset, MetricDef
from src.eval_workbench.domain.result import Result
from src.eval_workbench.domain.trace import MessagePart
from src.eval_workbench.services.benchmark import (
    render_markdown_report,
    select_cases,
)
from src.eval_workbench.services.errors import ServiceError
from src.eval_workbench.storage.kuzu_store import close_all, get_connection


def test_regression_stats():
    stats = regression_stats([100.0, 200.0], [110.0, 190.0])
    assert stats["n"] == 2
    assert stats["r2"] is not None


def test_classification_stats():
    stats = classification_stats([True, False, True], [True, True, False])
    assert stats["n"] == 3
    assert stats["f1"] is not None
    assert stats["confusion_matrix"] is not None


def test_select_cases_filters_by_tag(tmp_path):
    repo_path = str(tmp_path / "agent_repo")
    try:
        conn = get_connection(repo_path)
        from src.eval_workbench.storage.repositories import EvalCaseRepository, EvalDatasetRepository

        case_a = EvalCase(
            id="case_a",
            name="A",
            target_agent_path="agent:root",
            conversation=[MessagePart(role="user", kind="text", text="hi")],
            distribution_position="in",
            problem_type="happy",
            tags=["europe-trips"],
        )
        case_b = EvalCase(
            id="case_b",
            name="B",
            target_agent_path="agent:root",
            conversation=[MessagePart(role="user", kind="text", text="hi")],
            distribution_position="ood",
            problem_type="happy",
            tags=["mars"],
        )
        EvalCaseRepository(conn).save(case_a)
        EvalCaseRepository(conn).save(case_b)
        EvalDatasetRepository(conn).save(
            EvalDataset(id="ds1", name="DayTrip Tests Temp", case_ids=["case_a", "case_b", "case_a"])
        )

        selected = select_cases(conn, "DayTrip Tests Temp", ["europe-trips"])
        assert [c.id for c in selected] == ["case_a"]
    finally:
        close_all()


def test_render_markdown_report_includes_snapshot_and_scores():
    snapshot = {"id": "snap1", "agent_target": {"agent_path": "a:b"}}
    case = EvalCase(
        id="case1",
        name="Paris",
        target_agent_path="a:b",
        conversation=[],
        distribution_position="in",
        problem_type="happy",
    )
    from src.eval_workbench.services.benchmark import CaseRunOutcome

    outcomes = [
        CaseRunOutcome(
            case=case,
            results=[
                Result(name="budget_polite (polite)", type="bool", value=True, source="llm_judge"),
                Result(name="budget_correct", type="bool", value=True, source="deterministic"),
            ],
        )
    ]
    report = render_markdown_report(
        snapshot,
        outcomes,
        {"budget_polite (polite)": {"type": "bool", "average": 1.0, "n_true": 1, "n_false": 0, "n": 1}},
        {"budget_correct": {"kind": "bool", "precision": 1.0, "recall": 1.0, "f1": 1.0, "confusion_matrix": [[0, 0], [0, 1]], "n": 1}},
    )
    assert "# Eval Benchmark Report" in report
    assert "Paris" in report
    assert "budget_polite" in report
    assert "Rubric Summary" in report
    assert "Extractor Summary" in report


def test_run_headless_benchmark_integration_mocked(tmp_path):
    repo_path = str(tmp_path / "agent_repo")
    try:
        conn = get_connection(repo_path)
        from src.eval_workbench.storage.repositories import EvalCaseRepository, EvalDatasetRepository

        case = EvalCase(
            id="case1",
            name="Paris",
            target_agent_path="agent:root",
            conversation=[MessagePart(role="user", kind="text", text="Paris")],
            distribution_position="in",
            problem_type="happy",
            tags=["europe-trips"],
            metrics=[
                MetricDef(
                    id="m1",
                    name="budget_correct",
                    strategy="deterministic",
                    result_type="bool",
                    extractor_ref="ext1",
                    ground_truth="true",
                )
            ],
        )
        EvalCaseRepository(conn).save(case)
        EvalDatasetRepository(conn).save(
            EvalDataset(id="ds1", name="DayTrip Tests Temp", case_ids=["case1"])
        )
    finally:
        close_all()

    snapshot = {
        "id": "commit:agent:root",
        "agent_target": {"agent_path": "agent:root", "repo_path": repo_path, "name": "root"},
        "commit_hash": "commit",
    }
    run_payload = {
        "id": "run1",
        "trace": {
            "id": "trace1",
            "parts": [],
            "snapshot_id": snapshot["id"],
            "case_id": "case1",
            "model_id": "gemini-2.5-flash",
            "repetition_index": 0,
            "exception": None,
        },
    }
    scored_payload = {
        "results": [
            {"name": "budget_correct", "type": "bool", "value": True, "source": "deterministic"},
        ]
    }

    with (
        patch("src.eval_workbench.services.benchmark.agents_service.scan", return_value=snapshot),
        patch("src.eval_workbench.services.benchmark.runs_service.generate_run", return_value=run_payload),
        patch("src.eval_workbench.services.benchmark.runs_service.evaluate_run", return_value=scored_payload),
        patch("src.eval_workbench.services.benchmark._extractor_pairs", return_value=[]),
    ):
        from src.eval_workbench.services.benchmark import run_headless_benchmark

        report = run_headless_benchmark(
            repo_path=repo_path,
            agent_path="agent:root",
            commit="HEAD",
            dataset_name="DayTrip Tests Temp",
            tags=["europe-trips"],
        )
    assert "# Eval Benchmark Report" in report
    assert "budget_correct" in report

    with patch("src.eval_workbench.services.benchmark.agents_service.scan", return_value=snapshot):
        from src.eval_workbench.services.benchmark import run_headless_benchmark

        with pytest.raises(ServiceError):
            run_headless_benchmark(
                repo_path=repo_path,
                agent_path="agent:root",
                commit="HEAD",
                dataset_name="DayTrip Tests Temp",
                tags=["missing-tag"],
            )
