# Loop skills — inner loop (blueprint inside the eval framework)

These skills run the loop **inside** the eval workbench. Each skill tells the
calling LLM how to POST an `AgentBlueprint` (or a named preset) to
`/api/blueprints/run`; the framework instantiates a Google ADK `LlmAgent`,
resolves its tools from the shared registry, and runs it to completion.

Use these when you want the eval framework itself to own the loop. The calling
LLM decides whether to tweak the blueprint's `instruction`/`tools` before
running it.

Pair directory: `skills/loops_mcp/` — the same four loops expressed as tool
sequences for an autonomous coding agent that drives the workbench MCP directly
(the coding agent *is* the loop).

Loops: `ci_cd/`, `audit/`, `harness_optimisation/`, `adversarial/`.

See specs/design/contracts/loops_mcp_blueprints.md for the full contract.
