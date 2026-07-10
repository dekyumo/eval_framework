import pytest

from src.eval_workbench.runner.agentic_sim import (
    bind_gym_tools,
    load_gym,
    remap_role,
)

GYM_PATH = "tests.fixtures.gyms.simple_gym.CounterGym"


def test_load_gym_constructs_with_config():
    gym = load_gym(GYM_PATH, {"steps": 3})
    assert gym.remaining == 3


def test_bind_gym_tools_returns_bound_methods():
    gym = load_gym(GYM_PATH, {"steps": 2})
    decrement, is_done = bind_gym_tools(gym, ["decrement", "is_done"])

    assert decrement(1) == "remaining=1"
    assert gym.remaining == 1
    assert is_done() is False


def test_bind_gym_tools_missing_name_raises():
    gym = load_gym(GYM_PATH, {"steps": 1})
    with pytest.raises(AttributeError):
        bind_gym_tools(gym, ["nonexistent"])


def test_remap_role_assistant_to_user():
    assert remap_role({"role": "assistant", "kind": "text", "text": "hi"}) == {
        "role": "user",
        "kind": "text",
        "text": "hi",
    }


def test_remap_role_leaves_other_roles_untouched():
    for role in ("user", "tool", "system"):
        part = {"role": role, "kind": "text", "text": "x"}
        assert remap_role(part) == part


def test_termination_flips_after_decrements():
    gym = load_gym(GYM_PATH, {"steps": 2})
    termination = getattr(gym, "is_done")
    decrement = getattr(gym, "decrement")

    assert termination() is False
    decrement()
    assert termination() is False
    decrement()
    assert termination() is True
