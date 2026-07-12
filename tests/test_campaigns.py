import pytest

from src.eval_workbench.domain.result import Result
from src.eval_workbench.domain.rubric import Rubric, RubricItem
from src.eval_workbench.services.campaigns import (
    _collect_dataset_metrics,
    _find_scored_result,
)
from src.eval_workbench.services.errors import ServiceError
from src.eval_workbench.services.scoring import rubric_result_name


class _FakeCase:
    def __init__(self, metrics):
        self.metrics = metrics


class _FakeMetric:
    def __init__(self, name, strategy, result_type, rubric_ref=None):
        self.name = name
        self.strategy = strategy
        self.result_type = result_type
        self.rubric_ref = rubric_ref


class _FakeCaseRepo:
    def __init__(self, cases):
        self._cases = cases

    def get(self, case_id):
        return self._cases.get(case_id)


class _FakeRubricRepo:
    def __init__(self, rubrics):
        self._rubrics = rubrics

    def get(self, rubric_id):
        return self._rubrics.get(rubric_id)


def test_collect_dataset_metrics_flattens_rubric_items():
    rubric = Rubric(
        id="rubric_test",
        name="Quality",
        instructions="Be strict",
        items=[
            RubricItem(name="refused_request", type="float", prompt="Score"),
            RubricItem(name="appropriate", type="bool", prompt="OK?"),
        ],
        default_judge_prompt="Grade",
        version=1,
        fingerprint="fp",
    )
    case = _FakeCase([
        _FakeMetric("case_writer_rubric", "rubric", "float", rubric_ref="rubric_test"),
    ])
    metrics = _collect_dataset_metrics(
        _FakeCaseRepo({"case_1": case}),
        _FakeRubricRepo({"rubric_test": rubric}),
        ["case_1"],
    )
    names = {m["name"]: m["result_type"] for m in metrics}
    assert names == {
        rubric_result_name("case_writer_rubric", "appropriate"): "bool",
        rubric_result_name("case_writer_rubric", "refused_request"): "float",
    }


def test_find_scored_result_matches_rubric_result_name():
    full_name = rubric_result_name("case_writer_rubric", "refused_request")
    results = [
        Result(name=full_name, type="float", value=72.0, source="llm_judge"),
    ]
    assert _find_scored_result(results, full_name) is results[0]
    assert _find_scored_result(results, "refused_request") is results[0]


def test_find_scored_result_matches_deterministic_metric_name():
    results = [
        Result(name="budget_correct", type="bool", value=True, source="deterministic"),
    ]
    assert _find_scored_result(results, "budget_correct") is results[0]


def test_collect_dataset_metrics_missing_rubric_is_422():
    case = _FakeCase([
        _FakeMetric("quality", "rubric", "float", rubric_ref="missing_rubric"),
    ])
    with pytest.raises(ServiceError) as exc:
        _collect_dataset_metrics(
            _FakeCaseRepo({"case_1": case}),
            _FakeRubricRepo({}),
            ["case_1"],
        )
    assert exc.value.status_code == 422
