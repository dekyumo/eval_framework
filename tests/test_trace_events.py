from types import SimpleNamespace

from src.eval_workbench.runner.trace_events import (
    accumulate_token_usage,
    empty_token_totals,
)


def test_accumulate_token_usage_sums_across_events():
    totals = empty_token_totals()
    event_a = SimpleNamespace(
        usage_metadata=SimpleNamespace(
            prompt_token_count=120,
            candidates_token_count=45,
        )
    )
    event_b = SimpleNamespace(
        usage_metadata=SimpleNamespace(
            prompt_token_count=80,
            candidates_token_count=30,
        )
    )
    event_no_usage = SimpleNamespace(usage_metadata=None)

    accumulate_token_usage(totals, event_a)
    accumulate_token_usage(totals, event_b)
    accumulate_token_usage(totals, event_no_usage)

    assert totals == {"prompt": 200, "completion": 75, "total": 275}


def test_accumulate_token_usage_handles_missing_fields():
    totals = empty_token_totals()
    accumulate_token_usage(totals, SimpleNamespace(usage_metadata=SimpleNamespace()))
    assert totals == {"prompt": 0, "completion": 0, "total": 0}
