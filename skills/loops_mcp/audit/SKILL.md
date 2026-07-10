# Skill: Audit Loop (outer — MCP)

Use this skill when **you** (the autonomous coding agent) own the governance
audit loop. Drive the eval workbench MCP server directly.

Pair skill: `skills/loops_blueprint/audit/SKILL.md` (inner loop via API).

---

## 1. Connect to MCP

```bash
python run_app.py <repo> --mode mcp
```

Stdio server; repo path from `EVAL_WORKBENCH_REPO` (defaults to CWD).

---

## 2. What this loop does

Audit the latest agent snapshot:

- Distribution tags (in / margin / ood) match the stated domain.
- Problem-type tags (client / technical / adversarial) are appropriately placed.
- Governance safeguards (NIST concerns → tags → cases) are present and tested.
- Average token cost per run is computed and compared to the business justification.

Apply judgement per `skills/governance_audit/SKILL.md`.

---

## 3. Tool sequence

```
1. list_snapshots       → latest snapshot_id
2. get_snapshot         → AgentDistribution, domain description, governance blob
3. list_tags            → registry tags for cross-reference
4. list_cases           → all cases with tag assignments
5. get_case             → drill into suspicious cases (repeat)
6. get_governance       → concern_coverage prose + business_case
7. list_scored_runs     → token/cost fields per run
8. run_report           → optional full CSV if scored runs are stale
```

Group cases by distribution and problem-type tags. For each NIST concern in
Parse `concern_coverage` freeform text and cross-check tag names against `list_tags` and case tag assignments.

---

## 4. Stop condition ("until G")

**G** = audit report written with:

| Area | Output |
|---|---|
| Distribution | pass/flag per mis-tagged case |
| Problem types | coverage gaps listed |
| Safeguards | untested concerns flagged |
| Token cost | mean cost/run + comparison to business case |

---

## 5. Where you act on results

| Finding | Action |
|---|---|
| Mis-tagged cases | Edit case tags or move cases; use `create_case` / registry tools if creating replacements. |
| Untested safeguard | Create cases tagged for that concern (`generate_case`, `create_case`). |
| Stale governance | `update_governance` to fix tag mappings or business justification. |
| High token cost | Report to user; cost fixes are agent-code changes (outside this loop). |

Do not auto-approve governance — surface flags and let a human confirm before
bulk tag or governance edits.
