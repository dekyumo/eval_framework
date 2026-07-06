"""Recursive ADK agent structure extraction for the deterministic scanner."""

from __future__ import annotations

import hashlib
import inspect
from typing import Any

CALLBACK_ATTRS = (
    "before_model_callback",
    "after_model_callback",
    "on_model_error_callback",
    "before_tool_callback",
    "after_tool_callback",
    "on_tool_error_callback",
)

AGENT_FIELDS = (
    "name",
    "description",
    "model",
    "instruction",
    "output_key",
    "output_schema",
    "input_schema",
    "global_instruction",
    "static_instruction",
)


def fingerprint(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def _module_name(obj: Any) -> str:
    return getattr(obj, "__module__", "") or getattr(type(obj), "__module__", "") or ""


def is_adk_builtin(obj: Any) -> bool:
    mod = _module_name(obj)
    return mod.startswith("google.adk")


def is_agent_like(obj: Any) -> bool:
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return False

    mod = _module_name(obj)
    type_name = type(obj).__name__
    if "google.adk.agents" in mod and ("Agent" in type_name or hasattr(obj, "sub_agents")):
        return True

    return any(
        hasattr(obj, attr)
        for attr in ("tools", "sub_agents", "instruction")
    )


def _unwrap_callable(obj: Any) -> Any:
    for attr in ("func", "_func", "function"):
        inner = getattr(obj, attr, None)
        if callable(inner):
            return inner
    return obj


def _callable_name(obj: Any) -> str:
    if hasattr(obj, "name") and isinstance(getattr(obj, "name"), str):
        return obj.name
    if hasattr(obj, "__name__"):
        return obj.__name__
    return type(obj).__name__


def describe_callable(obj: Any) -> dict | None:
    if is_adk_builtin(obj):
        # TODO: agent as tool
        name = _callable_name(obj)
        return {
            "id": name,
            "name": name,
            "kind": "adk_builtin",
            "signature": "()",
            "source": None,
            "source_fingerprint": fingerprint(name),
            "module": _module_name(obj),
        }

    target = _unwrap_callable(obj)
    if not (inspect.isfunction(target) or inspect.ismethod(target)):
        if not callable(target):
            name = _callable_name(obj)
            return {
                "id": name,
                "name": name,
                "kind": "object",
                "signature": "()",
                "source": None,
                "source_fingerprint": fingerprint(name),
                "module": _module_name(obj),
            }
        target = obj

    name = _callable_name(target)
    try:
        signature = str(inspect.signature(target))
    except (TypeError, ValueError):
        signature = "()"

    source = ""
    try:
        source = inspect.getsource(target)
    except (OSError, TypeError):
        source = ""

    return {
        "id": name,
        "name": name,
        "kind": "function",
        "signature": signature,
        "source": source or None,
        "source_fingerprint": fingerprint(source) if source else fingerprint(name),
        "module": _module_name(target),
    }


def _get_instruction(agent: Any) -> str:
    instruction = getattr(agent, "instruction", None) or getattr(agent, "instructions", None) or ""
    if callable(instruction):
        return "<dynamic instruction provider>"
    return str(instruction) if instruction else ""


def _schema_label(schema: Any) -> str:
    if schema is None:
        return ""
    if hasattr(schema, "__name__"):
        return schema.__name__
    return type(schema).__name__


def _agent_fields_for_llm(agent: Any) -> dict:
    fields: dict[str, Any] = {"type": type(agent).__name__}
    for attr in AGENT_FIELDS:
        if attr in ("instruction"):
            continue
        value = getattr(agent, attr, None)
        if value is None:
            continue
        if attr in ("output_schema", "input_schema"):
            fields[attr] = _schema_label(value)
        elif attr == "model":
            fields["model"] = str(value)
        else:
            fields[attr] = value

    instruction = _get_instruction(agent)
    if instruction:
        fields["instruction"] = instruction
    return fields


def explore_agent(agent: Any, visited: set[int] | None = None) -> dict:
    if visited is None:
        visited = set()

    oid = id(agent)
    if oid in visited:
        return {"_ref": getattr(agent, "name", str(oid))}
    visited.add(oid)

    node = _agent_fields_for_llm(agent)
    node["tools"] = [
        tool
        for tool in (describe_callable(t) for t in (getattr(agent, "tools", None) or []))
        if tool is not None
    ]

    callbacks = []
    for attr in CALLBACK_ATTRS:
        callback = getattr(agent, attr, None)
        if callback is None:
            continue
        items = callback if isinstance(callback, list) else [callback]
        for item in items:
            info = describe_callable(item)
            if info is not None:
                info["callback_type"] = attr
                callbacks.append(info)
    node["callbacks"] = callbacks

    node["sub_agents"] = [
        explore_agent(sub_agent, visited)
        for sub_agent in (getattr(agent, "sub_agents", None) or [])
        if is_agent_like(sub_agent)
    ]
    return node


def _walk_structure(
    node: dict,
    agents: list[dict],
    tools_by_id: dict[str, dict],
    prompts_by_id: dict[str, dict],
    prompt_counter: list[int],
) -> None:
    name = node.get("name", "unknown")
    instruction = node.get("instruction", "")
    prompt_id = ""
    if instruction:
        prompt_counter[0] += 1
        prompt_id = f"prompt_{prompt_counter[0]}"
        prompts_by_id.setdefault(
            prompt_id,
            {
                "id": prompt_id,
                "fingerprint": fingerprint(instruction),
                "text": instruction,
            },
        )

    tool_ids = []
    for tool in node.get("tools", []):
        tool_id = tool["id"]
        tool_ids.append(tool_id)
        tools_by_id.setdefault(
            tool_id,
            {
                "id": tool_id,
                "name": tool["name"],
                "signature": tool.get("signature", "()"),
                "source_fingerprint": tool["source_fingerprint"],
                "reaches_external": False,
                "module": tool.get("module"),
                "source": tool.get("source"),
            },
        )

    hook_ids = []
    for callback in node.get("callbacks", []):
        hook_id = f"{callback.get('callback_type', 'callback')}:{callback['id']}"
        hook_ids.append(hook_id)

    subagent_names = [
        sub.get("name")
        for sub in node.get("sub_agents", [])
        if sub.get("name") and "_ref" not in sub
    ]
    agents.append(
        {
            "name": name,
            "model_id": str(node.get("model", "") or ""),
            "prompt_id": prompt_id,
            "tool_ids": tool_ids,
            "skill_ids": [],
            "hook_ids": hook_ids,
            "subagent_names": subagent_names,
        }
    )

    for sub in node.get("sub_agents", []):
        if "_ref" not in sub:
            _walk_structure(sub, agents, tools_by_id, prompts_by_id, prompt_counter)


def build_manifest_from_structure(structure: dict) -> tuple[list[dict], list[dict], list[dict]]:
    agents: list[dict] = []
    tools_by_id: dict[str, dict] = {}
    prompts_by_id: dict[str, dict] = {}
    _walk_structure(structure, agents, tools_by_id, prompts_by_id, [0])
    return agents, list(tools_by_id.values()), list(prompts_by_id.values())


def build_scan_result(agent: Any) -> dict:
    if not is_agent_like(agent):
        raise ValueError(f"Entrypoint is not agent-like: {type(agent)!r}")

    structure = explore_agent(agent)
    agents, tools, prompts = build_manifest_from_structure(structure)
    root_name = getattr(agent, "name", "root")

    return {
        "structure": structure,
        "agents": agents,
        "tools": tools,
        "models": [],
        "prompts": prompts,
        "root_agent_name": root_name,
    }
