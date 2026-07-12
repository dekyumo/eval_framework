import importlib.util
import inspect
import os
from pathlib import Path
from typing import Any

from src.eval_workbench.domain.fault import FaultConfig, ToolFault
from src.eval_workbench.faults.fault_mocker_runner import generate_mocked_tools
from src.eval_workbench.repo_layout import mocked_tools_path
from src.eval_workbench.scanner.agent_structure_dump import is_adk_builtin


class FaultTargetNotMockable(Exception):
    pass


class StateTracker:
    def __init__(self):
        self.call_counts = {}


class _ActiveToolFault:
    """Minimal fault context passed to mock functions."""

    def __init__(self, tool_fault: ToolFault):
        self.fault_class = tool_fault.fault_type
        self.target = tool_fault.tool_name


def _resolve_mocked_tools_path(
    fault_config: FaultConfig,
    agent_path: str,
    repo_path: str,
) -> Path:
    if fault_config.mocked_tools_ref and os.path.exists(fault_config.mocked_tools_ref):
        return Path(fault_config.mocked_tools_ref)

    canonical = mocked_tools_path(repo_path, agent_path)
    fault_config.mocked_tools_ref = str(canonical)
    return canonical


def ensure_mocked_tools(
    repo_path: str,
    agent: Any,
    agent_path: str,
    fault_config: FaultConfig | None = None,
) -> str:
    """Generate mocked_tools.py in the target repo's eval_framework directory if missing."""
    if fault_config:
        target_path = _resolve_mocked_tools_path(fault_config, agent_path, repo_path)
    else:
        target_path = mocked_tools_path(repo_path, agent_path)

    if not target_path.exists():
        generate_mocked_tools(repo_path, agent, agent_path)

    if fault_config:
        fault_config.mocked_tools_ref = str(target_path)
    return str(target_path)


def _load_mocks(mocked_tools_ref: str) -> dict:
    spec = importlib.util.spec_from_file_location("mocked_tools", mocked_tools_ref)
    if spec is None or spec.loader is None:
        return {}
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return getattr(mod, "MOCKS", {})


def _tool_name(tool: Any) -> str:
    if hasattr(tool, "name") and isinstance(tool.name, str):
        return tool.name
    if inspect.isfunction(tool) or callable(tool):
        return getattr(tool, "__name__", "tool")
    return type(tool).__name__


def _invoke_before_tool_callback(
    callback: Any,
    tool: Any,
    args: dict,
    tool_context: Any = None,
) -> Any:
    """Call an ADK before_tool_callback (tool, args, tool_context)."""
    return callback(tool=tool, args=args, tool_context=tool_context)


def _wrap_mock(mock_fn, active_fault: _ActiveToolFault):
    def wrapped(*args, **kwargs):
        if args:
            tool_args = args[0] if isinstance(args[0], dict) else kwargs
        else:
            tool_args = kwargs
        return mock_fn(tool_args, active_fault)

    wrapped.__name__ = getattr(mock_fn, "__name__", "mock_tool")
    return wrapped


def _replace_tools_on_agent(
    agent: Any,
    mocks: dict,
    tool_fault: ToolFault,
    active_fault: _ActiveToolFault,
) -> None:
    tools = getattr(agent, "tools", None)
    if tools is not None:
        new_tools = []
        for tool in tools:
            name = _tool_name(tool)
            if name == tool_fault.tool_name and name in mocks:
                if is_adk_builtin(tool):
                    new_tools.append(tool)
                else:
                    new_tools.append(_wrap_mock(mocks[name], active_fault))
            else:
                new_tools.append(tool)
        agent.tools = new_tools

    for sub in getattr(agent, "sub_agents", None) or []:
        _replace_tools_on_agent(sub, mocks, tool_fault, active_fault)


def apply_tool_fault(
    agent: Any,
    repo_path: str,
    agent_path: str,
    tool_fault: ToolFault,
) -> None:
    """Ensure mocked tools exist and swap the target tool on the agent tree."""
    mocked_tools_ref = ensure_mocked_tools(repo_path, agent, agent_path)
    mocks = _load_mocks(mocked_tools_ref)
    if tool_fault.tool_name not in mocks:
        raise FaultTargetNotMockable(
            f"Tool {tool_fault.tool_name!r} has no mock in {mocked_tools_ref}"
        )
    active_fault = _ActiveToolFault(tool_fault)
    _replace_tools_on_agent(agent, mocks, tool_fault, active_fault)
    _attach_tool_fault_callback(agent, mocks, tool_fault, active_fault)


def _attach_tool_fault_callback(
    agent: Any,
    mocks: dict,
    tool_fault: ToolFault,
    active_fault: _ActiveToolFault,
) -> None:
    """Intercept ADK builtin tools via before_tool_callback."""

    prior = getattr(agent, "before_tool_callback", None)

    def before_tool_callback(tool: Any, args: dict, tool_context: Any = None) -> Any:
        name = _tool_name(tool)
        if name == tool_fault.tool_name and name in mocks:
            return mocks[name](args, active_fault)
        if prior:
            return _invoke_before_tool_callback(prior, tool, args, tool_context)
        return None

    if hasattr(agent, "before_tool_callback"):
        agent.before_tool_callback = before_tool_callback

    for sub in getattr(agent, "sub_agents", None) or []:
        _attach_tool_fault_callback(sub, mocks, tool_fault, active_fault)


def register_fault_callbacks(
    agent: Any,
    fault_config: FaultConfig | None,
    repo_path: str,
    agent_path: str,
    mocked_tools_module_path: str | None = None,
) -> None:
    if not fault_config:
        return

    state = StateTracker()
    ensure_mocked_tools(repo_path, agent, agent_path, fault_config)

    mocked_tools_ref = mocked_tools_module_path or fault_config.mocked_tools_ref
    mocks = _load_mocks(mocked_tools_ref) if mocked_tools_ref and os.path.exists(mocked_tools_ref) else {}

    def before_tool_callback(tool: Any, args: dict, tool_context: Any = None) -> Any:
        tool_name = _tool_name(tool)
        state.call_counts[tool_name] = state.call_counts.get(tool_name, 0) + 1
        call_count = state.call_counts[tool_name]

        trigger_active = False
        if fault_config.target == tool_name:
            if fault_config.trigger == "always":
                trigger_active = True
            elif fault_config.trigger == "first_call" and call_count == 1:
                trigger_active = True
            elif fault_config.trigger == "nth_call" and fault_config.n == call_count:
                trigger_active = True

            if trigger_active and not fault_config.persistent:
                if call_count > 1 and fault_config.trigger == "always":
                    trigger_active = False

        if trigger_active:
            if fault_config.fault_class == "crash":
                raise RuntimeError(fault_config.payload or "Injected crash")
            if fault_config.fault_class == "omission":
                return None
            if fault_config.fault_class == "timing":
                import time
                time.sleep(float(fault_config.payload or 1.0))

        if tool_name in mocks:
            return mocks[tool_name](args, fault_config if trigger_active else None)

        if trigger_active and fault_config.fault_class not in ["crash", "omission", "timing"]:
            raise FaultTargetNotMockable(f"Tool {tool_name} has no mock implementation")

        return None

    _attach_callback(agent, before_tool_callback)


def _attach_callback(agent: Any, callback) -> None:
    if hasattr(agent, "before_tool_callback"):
        agent.before_tool_callback = callback
    for sub in getattr(agent, "sub_agents", None) or []:
        _attach_callback(sub, callback)
