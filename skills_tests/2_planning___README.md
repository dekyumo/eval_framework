# Skill tests — dual-MCP architecture

Goal: **properly test** `skills/loops_mcp/{audit,ci_cd,adversarial}` by planting
flaws in subject agents (L1), then evaluating *evaluating* agents (L2) that load
those skills via `SkillToolset`. Pass/fail is normal eval-framework scoring
(LLM-as-judge rubrics on semantic equivalence to planted flaws).

Harness optimisation is **out of scope**.

Human design prose: [`seven_agents_skill_fixtures.md`](./seven_agents_skill_fixtures.md).  
L1 seed contracts: [`manifests/*.json`](./manifests/) (injected via MCP as cases/tags/governance).

---

## Two repos (siblings of `eval_framework`)

| Repo | Role |
|------|------|
| `agents_evaluated_with_skills/` | L1 subject agents (7 packages). Own git. Baseline commit + regression commit. |
| `agents_evaluating_with_skills/` | L2 loop agents: `audit_runner`, `ci_cd_runner`, `adversarial_runner`. `SkillToolset` → files in **this** repo (`skills/loops_mcp/...`). |

Skills stay in **`eval_framework/skills/loops_mcp/`** (single source of truth). L2 points at those paths. We improve skills → re-run L2 → improve again.

---

## Cursor MCP juggling (required)

L1 and L2 MCP advertise the **same** tool names. Cursor can only attach **one** at a time.

| Phase | Cursor MCP | What Grok does |
|-------|------------|----------------|
| A | **L1** | Seed L1 from JSON manifests; scan; run/score; apply regression commit; note commit hashes + snapshot ids |
| — | **PAUSE** | You disconnect L1 MCP, start L2 web+MCP, connect Cursor to L2 |
| B | **L2** | Seed L2 cases (skill-used + semantic equivalence); run L2 agents; iterate skills until judges pass |

L1 Flask can stay up while Cursor is on L2 so L2 agents’ `McpToolset` can still reach L1’s API (child process / URL — not Cursor’s MCP session).

---

## Phase A — L1 subjects

1. Scaffold monorepo `agents_evaluated_with_skills` with 7 simple ADK agents (`gemini-2.5-flash`, plain Python tools — no gym / advanced mock pipeline).
2. Commit until baseline works; **note baseline commit**.
3. You: `python run_app.py <L1> ` + MCP; connect Cursor to L1.
4. Seed via MCP from `skills_tests/manifests/*.json`.
5. Scan baseline, generate/evaluate runs.
6. Patch per fixture CI sections; commit until regression works; **note regression commit**; scan that commit only.
7. Snapshot only those two commits.

Dirty tree: **commit before scan** (no framework change).

---

## Phase B — L2 evaluators

1. Scaffold L2 agents with `SkillToolset` loading `eval_framework/skills/loops_mcp/<loop>/` and tools to drive L1.
2. You: disconnect L1 MCP; start L2 web+MCP; connect Cursor to L2.
3. Seed L2: for each (L1 agent × {audit, ci_cd, adversarial}) create eval cases + rubrics that score:
   - skill was loaded/used (`SkillToolset` tool calls in the trace), and
   - findings ≈ planted flaws in `seven_agents_skill_fixtures.md` (LLM judge).
4. Run / score. Failures → edit skills in **main** `skills/loops_mcp/` → re-run until green.

No separate “skill report” artefact — the L2 eval run *is* the test.

---

## What manifests are

JSON under `manifests/` = **seed payload for L1 MCP** (tags, case names, distribution tags, governance prose, CI broken-case ids). Not a pytest oracle.

---

## Open run notes (fill during Phase A)

```
L1 repo path:
L1 baseline commit:
L1 regression commit:
L1 baseline snapshot ids (per agent):
L1 regression snapshot ids (per agent):
L2 repo path:
```
