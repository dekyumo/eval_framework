"""Two-agent gym simulation (tau-bench style) for agentic-user eval cases.

A simulated user agent and the solver agent take turns until the gym's
termination predicate returns True or `max_turns` is reached. Gym bound
methods are injected as tools into either agent.
"""

from __future__ import annotations

import importlib
from typing import Any

from google.adk.runners import InMemoryRunner
from google.genai import types

from src.eval_workbench.runner.trace_events import (
    accumulate_token_usage,
    append_trace_parts_from_event,
    empty_token_totals,
)


def load_gym(class_path: str, config: dict) -> Any:
    """Instantiate a gym class `module.path.ClassName` with a config dict."""
    module_path, class_name = class_path.rsplit(".", 1)
    module = importlib.import_module(module_path)
    cls = getattr(module, class_name)
    return cls(config)


def load_agent(agent_path: str) -> Any:
    """Import an agent via `module.path:variable`."""
    module_path, var_name = agent_path.split(":")
    module = importlib.import_module(module_path)
    return getattr(module, var_name)


def bind_gym_tools(gym: Any, names: list[str]) -> list:
    """Return the gym's bound methods for the given names (ADK tools)."""
    tools = []
    for name in names:
        if not hasattr(gym, name):
            raise AttributeError(f"Gym {type(gym).__name__} has no tool method {name!r}")
        tools.append(getattr(gym, name))
    return tools


def inject_tools(agent: Any, tools: list) -> None:
    """Append tools to an agent's tool list, creating it if absent."""
    if not tools:
        return
    existing = getattr(agent, "tools", None)
    if existing is None:
        agent.tools = list(tools)
    else:
        agent.tools = list(existing) + list(tools)


def remap_role(part: dict) -> dict:
    """Copy a trace part, relabelling an assistant role as user."""
    remapped = dict(part)
    if remapped.get("role") == "assistant":
        remapped["role"] = "user"
    return remapped


async def _run_one(
    runner: InMemoryRunner,
    session_id: str,
    text: str,
    trace_parts: list,
    token_totals: dict,
    *,
    as_user: bool = False,
) -> str:
    """Run one agent turn, record parts/tokens, and return its final text."""
    new_msg = types.Content(role="user", parts=[types.Part.from_text(text=text)])
    turn_parts: list = []
    final_text = ""
    async for event in runner.run_async(
        user_id="user1",
        session_id=session_id,
        new_message=new_msg,
    ):
        accumulate_token_usage(token_totals, event)
        append_trace_parts_from_event(event, turn_parts)
        if event.is_final_response() and event.message:
            final_text = "".join(part.text for part in event.message.parts if part.text)

    if as_user:
        turn_parts = [remap_role(part) for part in turn_parts]
    trace_parts.extend(turn_parts)
    return final_text


async def run_agentic_simulation(
    *,
    solver_agent: Any,
    agentic_user: dict,
    session_state: dict,
    seed_user_text: str,
    model_id: str,
    gym_class_path: str,
) -> tuple[list, dict]:
    """Alternate a simulated user and the solver agent within a gym."""
    gym_config = session_state.get("gym", {})
    solver_state = {k: v for k, v in session_state.items() if k != "gym"}

    gym = load_gym(gym_class_path, gym_config)
    user_agent = load_agent(agentic_user["user_agent_path"])

    for agent in (solver_agent, user_agent):
        if hasattr(agent, "model"):
            agent.model = model_id

    inject_tools(solver_agent, bind_gym_tools(gym, agentic_user["solver_tools"]))
    inject_tools(user_agent, bind_gym_tools(gym, agentic_user["user_tools"]))

    solver_runner = InMemoryRunner(agent=solver_agent, app_name="eval_workbench")
    user_runner = InMemoryRunner(agent=user_agent, app_name="eval_workbench")
    await solver_runner.session_service.create_session(
        app_name="eval_workbench",
        user_id="user1",
        session_id="solver_session",
        state=solver_state,
    )
    await user_runner.session_service.create_session(
        app_name="eval_workbench",
        user_id="user1",
        session_id="user_session",
    )

    trace_parts: list = [{"role": "user", "kind": "text", "text": seed_user_text}]
    token_totals = empty_token_totals()

    termination = getattr(gym, agentic_user["termination_method"])
    current_user_text = seed_user_text
    max_turns = agentic_user["max_turns"]

    turns = 0
    while not termination() and turns < max_turns:
        solver_text = await _run_one(
            solver_runner, "solver_session", current_user_text, trace_parts, token_totals
        )
        if termination():
            break
        current_user_text = await _run_one(
            user_runner, "user_session", solver_text, trace_parts, token_totals, as_user=True
        )
        turns += 1

    return trace_parts, token_totals
