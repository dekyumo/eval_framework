from src.eval_workbench.domain.gym import Gym
from src.eval_workbench.domain.rubric import Rubric
from src.eval_workbench.domain.tag import Tag
from src.eval_workbench.services import registries as registries_service


def test_rubric_field_description_round_trip(tmp_path):
    repo_path = str(tmp_path)
    rubric = Rubric.model_validate({
        "id": "rubric_test",
        "name": "Test Rubric",
        "instructions": "Grade it",
        "items": [{"name": "is_good", "type": "bool", "prompt": "Was the answer good?"}],
        "default_judge_prompt": "Judge: {instructions}",
        "version": 1,
        "fingerprint": "test",
        "frozen": False,
    })
    created = registries_service.create_rubric(repo_path, rubric)

    assert created.items[0].prompt == "Was the answer good?"

    listed = registries_service.list_rubrics(repo_path)
    assert listed[0].items[0].prompt == "Was the answer good?"


def test_create_gym_round_trip(tmp_path):
    repo_path = str(tmp_path)
    gym = Gym.model_validate({
        "id": "test-gym",
        "name": "Test Gym",
        "class_path": "tests.fixtures.gyms.simple_gym.CounterGym",
        "description": "fixture gym",
    })
    created = registries_service.create_gym(repo_path, gym)
    assert created.id == "test-gym"
    assert created.class_path == "tests.fixtures.gyms.simple_gym.CounterGym"

    listed = registries_service.list_gyms(repo_path)
    assert any(g.id == "test-gym" for g in listed)


def test_mcp_registry_exposes_gym_tools(tmp_path):
    from src.eval_workbench.mcp.registry_internal import build_internal_registry

    registry = build_internal_registry(str(tmp_path))
    assert "list_gyms" in registry
    assert "create_gym" in registry
    gym = registry["create_gym"](
        Gym(
            id="mcp-gym",
            name="MCP Gym",
            class_path="tests.fixtures.gyms.simple_gym.CounterGym",
        )
    )
    assert gym.id == "mcp-gym"
    assert registry["list_gyms"]()[0].id == "mcp-gym"
