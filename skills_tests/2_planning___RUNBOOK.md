# Skill-test runbook — MCP switch points

## Before anything

- Working tree of `eval_framework` can be dirty; L1/L2 agent repos must be **committed** before each `scan_agent`.
- Model for all agents: `gemini-2.5-flash`.
- Skills SoT: `eval_framework/skills/loops_mcp/{audit,ci_cd,adversarial}/SKILL.md`.

## Phase A — until PAUSE

1. Create `../agents_evaluated_with_skills` (monorepo, 7 agents).
2. Baseline commit → record hash below.
3. **YOU:** start L1 web + MCP; point Cursor MCP at L1 only.
4. Tell Grok “L1 MCP connected” → seed + scan + run.
5. Regression commit → record hash → scan regression only.

```
L1_REPO=c:\Users\Raph\Prj\kaggle_ai_agent_course\agents_evaluated_with_skills
BASELINE_COMMIT=67baf31230fbdb33a1e5f4982c87436cd7bf5266
# prior ToolContext: a42911ce1a5fd5354a9ae2cffd77401ab9a817e9
REGRESSION_COMMIT=26115fdae334c5dca84b50046b821e6ec3bb0636
```

## PAUSE 1 — switch MCP

1. Leave L1 **web** running on port 5000 (L2 agents spawn L1 MCP as a child → HTTP `:5000`).
2. Disconnect Cursor from L1 MCP.
3. Start L2 web on port 5001 + point Cursor MCP at L2 only.

Windows (PowerShell) — never use Linux `VAR=value cmd` prefixes:

```powershell
# L1 web (keep running)
$env:PYTHONPATH="c:\Users\Raph\Prj\kaggle_ai_agent_course\eval_framework\src"
python c:\Users\Raph\Prj\kaggle_ai_agent_course\eval_framework\run_app.py `
  c:\Users\Raph\Prj\kaggle_ai_agent_course\agents_evaluated_with_skills

# L2 web
$env:PYTHONPATH="c:\Users\Raph\Prj\kaggle_ai_agent_course\eval_framework\src"
python c:\Users\Raph\Prj\kaggle_ai_agent_course\eval_framework\run_app.py `
  c:\Users\Raph\Prj\kaggle_ai_agent_course\agents_evaluating_with_skills --port 5001
```

Cursor `mcp.json` for Phase B (L2):
- repo arg = `agents_evaluating_with_skills`
- `--api-url http://127.0.0.1:5001` (and/or `EVAL_WORKBENCH_API_URL` in the `env` block)

4. Restart Cursor MCP / reload so it picks up the config.
5. Tell Grok “L2 MCP connected”.

## Phase B

1. Scaffold/seed L2 agents + cases/rubrics.
2. Run L2 evals; edit `skills/loops_mcp/*` until judges pass.

## PAUSE 2 (optional)

If you need to re-seed L1 after skill/fixture changes: disconnect L2 MCP, reconnect L1 MCP, tell Grok.
