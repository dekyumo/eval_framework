from unittest.mock import patch

import asyncio
import pytest

from src.eval_workbench.domain.blueprint import AgentBlueprint, BlueprintPreset, BlueprintRunResult, ToolCall
from src.eval_workbench.mcp.tool_defs import TOOL_NAMES
from src.eval_workbench.mcp.registry_internal import build_internal_registry, resolve_tools
from src.eval_workbench.services import blueprints as blueprints_service
from src.eval_workbench.services.errors import ServiceError


def test_list_presets_returns_all_building_blocks():
    presets = blueprints_service.list_presets()
    assert len(presets) == len(BlueprintPreset)
    names = {item.preset for item in presets}
    assert names == {preset.value for preset in BlueprintPreset}
    for item in presets:
        assert item.instruction
        assert isinstance(item.tools, list)
        assert item.tools


def test_preset_blueprint_scanner():
    blueprint = blueprints_service.preset_blueprint("Scanner")
    assert blueprint.agent_name == "Scanner"
    assert blueprint.tools == ["scan_agent", "get_snapshot", "list_snapshots"]
    assert blueprint.instruction


def test_preset_blueprint_unknown_raises():
    with pytest.raises(ServiceError) as exc:
        blueprints_service.preset_blueprint("NotAPreset")
    assert exc.value.status_code == 400


def test_run_blueprint_unknown_tool_raises(tmp_path):
    with pytest.raises(ServiceError) as exc:
        blueprints_service.run_blueprint(
            str(tmp_path),
            AgentBlueprint(
                agent_name="test",
                instruction="do things",
                tools=["no_such_tool"],
            ),
        )
    assert exc.value.status_code == 400
    assert "Unknown tool" in exc.value.message


def test_run_blueprint_with_stubbed_runner(tmp_path):
    blueprint = AgentBlueprint(
        agent_name="reader",
        instruction="List tags.",
        tools=["list_tags"],
    )
    expected = BlueprintRunResult(
        blueprint=blueprint,
        final_output="Done listing tags.",
        transcript=[
            {"role": "assistant", "text": "Called list_tags({})"},
            {"role": "tool", "text": "list_tags: [{\"id\": \"t1\"}]"},
            {"role": "assistant", "text": "Done listing tags."},
        ],
        tool_calls=[ToolCall(name="list_tags", args={}, result='[{"id": "t1"}]')],
    )

    def fake_list_tags() -> list[dict]:
        return [{"id": "t1", "name": "test"}]

    with (
        patch(
            "src.eval_workbench.services.blueprints.resolve_tools",
            return_value=[fake_list_tags],
        ),
        patch(
            "src.eval_workbench.services.blueprints._run_blueprint_async",
            return_value=expected,
        ) as run_async,
    ):
        result = blueprints_service.run_blueprint(str(tmp_path), blueprint)

    run_async.assert_awaited_once()
    assert result.final_output == "Done listing tags."
    assert result.transcript
    assert result.tool_calls
    assert result.tool_calls[0].name == "list_tags"
    assert result.tool_calls[0].result


def test_tool_calls_from_trace_pairs_repeated_tools_in_order():
    trace_parts = [
        {"kind": "tool_call", "tool_name": "foo", "tool_args": {"i": 1}},
        {"kind": "tool_call", "tool_name": "foo", "tool_args": {"i": 2}},
        {"kind": "tool_response", "tool_name": "foo", "tool_response": "first"},
        {"kind": "tool_response", "tool_name": "foo", "tool_response": "second"},
    ]
    calls = blueprints_service._tool_calls_from_trace(trace_parts)
    assert len(calls) == 2
    assert calls[0].args == {"i": 1}
    assert calls[0].result == "first"
    assert calls[1].args == {"i": 2}
    assert calls[1].result == "second"


def test_run_blueprint_from_running_event_loop(tmp_path):
    blueprint = AgentBlueprint(
        agent_name="reader",
        instruction="List tags.",
        tools=["list_tags"],
    )
    expected = BlueprintRunResult(
        blueprint=blueprint,
        final_output="Done.",
        transcript=[],
        tool_calls=[],
    )

    async def invoke_from_loop() -> BlueprintRunResult:
        with patch(
            "src.eval_workbench.services.blueprints.resolve_tools",
            return_value=[lambda: []],
        ), patch(
            "src.eval_workbench.services.blueprints._run_blueprint_async",
            return_value=expected,
        ):
            return blueprints_service.run_blueprint(str(tmp_path), blueprint)

    result = asyncio.run(invoke_from_loop())
    assert result.final_output == "Done."
