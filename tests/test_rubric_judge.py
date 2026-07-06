from unittest.mock import patch

import pytest
from pydantic import BaseModel, Field

from src.eval_workbench.domain.rubric import Rubric, RubricItem
from src.eval_workbench.domain.trace import MessagePart, Trace
from src.eval_workbench.services.rubric_judge_runner import (
    build_rubric_output_schema,
    format_trace_for_judge,
)
from src.eval_workbench.services.scoring import RubricEvaluator
from src.eval_workbench.domain.case import EvalCase, MetricDef


def test_format_trace_for_judge_is_plain_text():
    trace = Trace(
        id="t1",
        parts=[
            MessagePart(role="user", kind="text", text="Hello"),
            MessagePart(role="assistant", kind="text", text="Hi there"),
            MessagePart(role="user", kind="media", media_mime="image/png", text="photo.png"),
        ],
        snapshot_id="s1",
        case_id="c1",
        model_id="gemini-2.5-flash",
    )
    text = format_trace_for_judge(trace)
    assert "[user]: Hello" in text
    assert "[assistant]: Hi there" in text
    assert "[attached media image/png]" in text
    assert "{" not in text


def test_build_rubric_output_schema_on_the_fly():
    rubric = Rubric(
        id="rubric_test",
        name="Quality",
        instructions="Be strict",
        items=[
            RubricItem(name="is_achievable", type="bool", prompt="Was the plan realistic?"),
            RubricItem(name="score", type="float", prompt="Overall score 0-100"),
        ],
        default_judge_prompt="Grade using {instructions}",
        version=1,
        fingerprint="fp",
    )
    schema_a = build_rubric_output_schema(rubric)
    schema_b = build_rubric_output_schema(rubric)
    assert schema_a is not schema_b
    assert "is_achievable" in schema_a.model_fields
    assert schema_a.model_fields["is_achievable"].annotation is bool
    assert schema_a.model_fields["score"].annotation is float
    assert "rationale" in schema_a.model_fields


def test_rubric_evaluator_uses_adk_judge():
    rubric = Rubric(
        id="rubric_test",
        name="Quality",
        instructions="Be strict",
        items=[RubricItem(name="is_achievable", type="bool", prompt="Was the plan realistic?")],
        default_judge_prompt="Grade using {instructions}",
        version=1,
        fingerprint="fp",
    )

    class FakeScore(BaseModel):
        is_achievable: bool = Field(description="Was the plan realistic?")
        rationale: str = Field(description="why")

    fake = FakeScore(is_achievable=True, rationale="Looks good")
    trace = Trace(
        id="t1",
        parts=[MessagePart(role="assistant", kind="text", text="Paris plan")],
        snapshot_id="s1",
        case_id="c1",
        model_id="gemini-2.5-flash",
    )
    case = EvalCase(
        id="c1",
        target_agent_path="a:b",
        conversation=[],
        distribution_position="in",
        problem_type="happy",
        metrics=[
            MetricDef(
                id="m1",
                name="budget_polite",
                strategy="rubric",
                result_type="bool",
                rubric_ref="rubric_test",
            )
        ],
    )

    with (
        patch("src.eval_workbench.services.scoring.RubricRepository") as repo_cls,
        patch(
            "src.eval_workbench.services.scoring.judge_trace_with_rubric",
            return_value=fake,
        ) as judge_mock,
    ):
        repo_cls.return_value.get.return_value = rubric
        results = RubricEvaluator().evaluate(trace, case, case.metrics[0], conn=None)

    judge_mock.assert_called_once_with(rubric, trace)
    assert len(results) == 1
    assert results[0].name == "budget_polite (is_achievable)"
    assert results[0].value is True
    assert results[0].source == "llm_judge"


@pytest.mark.parametrize(
    "item_type,raw,expected",
    [
        ("bool", False, False),
        ("int", 3, 3),
        ("float", 88.5, 88.5),
        ("enum", "good", "good"),
    ],
)
def test_rubric_evaluator_coerces_types(item_type, raw, expected):
    rubric = Rubric(
        id="rubric_test",
        name="Quality",
        instructions="",
        items=[RubricItem(name="field", type=item_type, prompt="desc")],
        default_judge_prompt="",
        version=1,
        fingerprint="fp",
    )
    schema = build_rubric_output_schema(rubric)
    payload = {"field": raw, "rationale": "ok"}
    parsed = schema.model_validate(payload)

    trace = Trace(
        id="t1",
        parts=[],
        snapshot_id="s1",
        case_id="c1",
        model_id="gemini-2.5-flash",
    )
    case = EvalCase(
        id="c1",
        target_agent_path="a:b",
        conversation=[],
        distribution_position="in",
        problem_type="happy",
        metrics=[
            MetricDef(
                id="m1",
                name="metric",
                strategy="rubric",
                result_type=item_type,
                rubric_ref="rubric_test",
            )
        ],
    )

    with (
        patch("src.eval_workbench.services.scoring.RubricRepository") as repo_cls,
        patch(
            "src.eval_workbench.services.scoring.judge_trace_with_rubric",
            return_value=parsed,
        ),
    ):
        repo_cls.return_value.get.return_value = rubric
        results = RubricEvaluator().evaluate(trace, case, case.metrics[0], conn=None)

    assert results[0].value == expected
