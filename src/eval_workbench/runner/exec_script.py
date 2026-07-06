import sys
import json
import importlib
import traceback
import asyncio
import time
import os

import dotenv

dotenv.load_dotenv()

from src.eval_workbench.ssl_config import configure_process_ssl

configure_process_ssl()

from datetime import datetime
from google.genai import types
from google.adk.runners import InMemoryRunner
from src.eval_workbench.runner.message_parts import build_genai_parts
from src.eval_workbench.runner.case_input import (
    build_structured_input_message,
    filter_input_payload,
    structured_input_trace_part,
)
from src.eval_workbench.runner.trace_events import (
    accumulate_token_usage,
    append_trace_parts_from_event,
    empty_token_totals,
)


def _build_trace(
    *,
    trace_parts: list,
    token_totals: dict[str, int],
    latency_ms: float,
    snapshot: dict,
    case: dict,
    model_id: str,
    fault_config: dict | None,
    exception: str | None = None,
) -> dict:
    return {
        "id": f"trace_{datetime.now().timestamp()}",
        "parts": trace_parts,
        "structured_output": None,
        "exception": exception,
        "latency_ms": latency_ms,
        "tokens": token_totals,
        "snapshot_id": snapshot["id"],
        "case_id": case["id"],
        "model_id": model_id,
        "repetition_index": 0,
        "fault_config_id": fault_config["id"] if fault_config else None,
    }


async def _consume_runner_events(runner, new_msg, trace_parts: list, token_totals: dict) -> None:
    async for event in runner.run_async(
        user_id="user1",
        session_id="session1",
        new_message=new_msg,
    ):
        accumulate_token_usage(token_totals, event)
        append_trace_parts_from_event(event, trace_parts)


async def run_agent_flow():
    with open(sys.argv[1], 'r') as f:
        snapshot = json.load(f)
    with open(sys.argv[2], 'r') as f:
        case = json.load(f)

    model_id = sys.argv[3]

    fault_config = None
    if sys.argv[4] != "null":
        with open(sys.argv[4], 'r') as f:
            fault_config = json.load(f)

    agent_target = snapshot["agent_target"]
    mod_name, var_name = agent_target["agent_path"].split(':')
    mod = importlib.import_module(mod_name)
    agent = getattr(mod, var_name)

    agent_path = agent_target["agent_path"]
    repo_path = agent_target["repo_path"]

    tool_fault_data = case.get("tool_fault")
    if tool_fault_data:
        from src.eval_workbench.domain.fault import ToolFault
        from src.eval_workbench.faults.injector import apply_tool_fault

        apply_tool_fault(agent, repo_path, agent_path, ToolFault.model_validate(tool_fault_data))
    elif fault_config:
        from src.eval_workbench.domain.fault import FaultConfig
        from src.eval_workbench.faults.injector import register_fault_callbacks

        fc = FaultConfig.model_validate(fault_config)
        register_fault_callbacks(agent, fc, repo_path, agent_path)

    if hasattr(agent, "model"):
        agent.model = model_id

    trace_parts: list = []
    token_totals = empty_token_totals()

    runner = InMemoryRunner(agent=agent, app_name="eval_workbench")
    session_state = case.get("session_state") or {}
    await runner.session_service.create_session(
        app_name="eval_workbench",
        user_id="user1",
        session_id="session1",
        state=session_state,
    )

    input_payload = case.get("input_payload")
    messages = case.get("conversation", [])

    start_time = time.time()

    try:
        if input_payload:
            if messages:
                raise ValueError("Eval case cannot set both input_payload and conversation turns")
            filtered_payload = filter_input_payload(agent, input_payload)
            trace_parts.append(structured_input_trace_part(filtered_payload))
            new_msg = build_structured_input_message(filtered_payload)
            await _consume_runner_events(runner, new_msg, trace_parts, token_totals)
        else:
            idx = 0
            while idx < len(messages):
                message = messages[idx]
                role = message.get("role", "user")
                if role not in ("user", "user_media"):
                    idx += 1
                    continue

                batch_parts: list[types.Part] = []
                while idx < len(messages) and messages[idx].get("role", "user") in ("user", "user_media"):
                    genai_parts, trace_part = build_genai_parts(messages[idx])
                    batch_parts.extend(genai_parts)
                    trace_parts.append(trace_part)
                    idx += 1

                new_msg = types.Content(role="user", parts=batch_parts)
                await _consume_runner_events(runner, new_msg, trace_parts, token_totals)

        latency = (time.time() - start_time) * 1000.0
        print(json.dumps(_build_trace(
            trace_parts=trace_parts,
            token_totals=token_totals,
            latency_ms=latency,
            snapshot=snapshot,
            case=case,
            model_id=model_id,
            fault_config=fault_config,
        )))

    except Exception:
        latency = (time.time() - start_time) * 1000.0
        print(json.dumps(_build_trace(
            trace_parts=trace_parts,
            token_totals=token_totals,
            latency_ms=latency,
            snapshot=snapshot,
            case=case,
            model_id=model_id,
            fault_config=fault_config,
            exception=traceback.format_exc(),
        )))


def main():
    if len(sys.argv) < 5:
        sys.exit(1)
    asyncio.run(run_agent_flow())

if __name__ == "__main__":
    main()
