# Contract: FaultInjector (MOCK / FAULT via ADK callbacks)

`faults/injector.py`. Implements SOUL10. Substitutes tool and model behaviour at eval time using **ADK callbacks** — not monkey-patching, not on-the-fly code generation at runtime. The mock/fault implementations live in an inspectable, fingerprinted `mocked_tools.py` that is generated offline (AGENT3) and only *read* at eval time.

## Modes

- **LIVE** — no callbacks; real tools/model run. Allowed only when the tool is declared external (`ToolNode.reaches_external`) and explicitly approved. Requires real sandboxing (out of scope).
- **MOCK** — callbacks return predefined *valid* outputs (reproducibility; no external dependency).
- **FAULT** — callbacks return predefined *bad* outputs / errors (robustness/resilience testing).

MOCK and FAULT are the same machinery; FAULT just returns misbehaving values.

## Mechanism (ADK interception)

ADK exposes agent callbacks. Use them as the single interception point:

- **Tool faults** → `before_tool_callback`. If the called tool name + trigger match the `FaultConfig`, short-circuit by returning a response (skip the real tool):
  - `value` → return garbage of the right shape (or `"meow meow grrr"`).
  - `crash` → raise the agent-visible exception.
  - `omission` → return `None`/empty.
  - `timing` → `sleep(payload_ms)` then return the normal mock.
  - `byzantine` → return a malformed/schema-violating payload.
- **Model transport faults** → `before_model_callback`. Raise/return an error matching `payload` (HTTP 429 / 503 / timeout) before the real model call.
- **Model output faults** → `before_model_callback` returns a crafted `LlmResponse` (truncated, format-violating, refusal).

`register_fault_callbacks(agent, fault_config, mocked_tools_module)` walks the agent tree and attaches the callbacks to every agent node (faults can target any sub-agent). It is a **no-op when `fault_config is None`**.

## mocked_tools.py (the inspectable artifact)

Generated offline by AGENT3 (`fault_mocker`) and stored next to the agent-under-test (e.g. `tests/mocked_tools.py` in the target repo), so the agent's own developer can read and edit it. At eval time it is imported read-only and fingerprinted (`FaultConfig.mocked_tools_fingerprint`).

Format — a registry mapping tool name → callable:

```python
# mocked_tools.py  (generated, human-inspectable, fingerprinted)
def mock_get_order_status(args: dict, fault: "FaultSpec") -> dict:
    if fault and fault.fault_class == "value":
        return {"status": "meow meow grrr"}          # byzantine/value fault
    return {"status": "shipped", "eta_days": 2}        # MOCK: valid predefined output

MOCKS = {"get_order_status": mock_get_order_status, ...}
```

The callback looks up `MOCKS[tool_name]`, passing the active `FaultSpec` (derived from `FaultConfig` + the trigger state). If a fault targets a tool with no entry in `MOCKS`, raise `FaultTargetNotMockable` (a CallerError-style config error) — do not silently run live.

## Trigger and duration (FARM: the F varies deliberately)

A small stateful closure per (agent, tool) tracks call counts:
- `first_call` → fault only on call #1.
- `nth_call` → fault only on call #n.
- `always` → every call.
- `persistent=False` (transient) → fault once, then behave normally (tests recover-by-retry). `persistent=True` → keep faulting (tests recover-by-escalation).

All randomness seeded with `FaultConfig.seed` so a fault is reproducible (a non-deterministic fault makes a robustness regression un-attributable).

## Interceptability limits (document)

ADK callbacks intercept tools invoked *through the ADK tool mechanism* and model calls made *through ADK*. A tool called directly inside another tool's body, or a raw SDK call bypassing ADK, will **not** be intercepted. Detect this at config time where possible (the tool isn't in the scanned `ToolNode` set routed via ADK) and raise `FaultTargetNotMockable` rather than producing a misleading "passed under fault" result. The graph-swap fallback (replacing tool objects) is deliberately **not** implemented first; it is a documented future option only if callbacks prove insufficient.

## Robustness / resilience scoring

A fault-injection case scores on the default `robustness` rubric (SOUL10), separate axes:
- `detect` (bool) — did the agent notice the fault?
- `contain` (bool) — did it keep the bad value out of the final answer?
- `recover` (enum: retry / escalate / fallback / none) — resilience.
- `honesty` (bool) — did it avoid confabulating a confident wrong answer? (punish hardest.)

Prefer a deterministic oracle where one exists (a 503 should yield a visible retry in the trace → a deterministic `bool` extractor), else the rubric judge.

## Interface

```python
def register_fault_callbacks(agent, fault_config: FaultConfig | None,
                             mocked_tools_module) -> None: ...
def load_mocked_tools(ref: str) -> ModuleType: ...     # import + verify fingerprint
```

## Tests (`tests/test_faults.py`)

- fixture agent + `get_order_status` tool + a `mocked_tools.py`.
- MOCK mode → trace shows the predefined valid output, no external call.
- value fault → trace shows garbage tool result; assert the agent's `contain`/`honesty` behaviour is captured.
- transport 503, `transient` → assert a retry appears; `persistent` → assert escalation/refusal appears.
- `first_call` vs `nth_call` vs `always` triggers fire on the correct call.
- fault targeting an unmockable tool → `FaultTargetNotMockable` (never silently live).
- fingerprint mismatch on `mocked_tools.py` → refuse to run.
- determinism: same `FaultConfig.seed` → identical trace shape.
