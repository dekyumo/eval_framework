# Skill: Audit Loop (inner — blueprint)

Use this skill to run a governance and coverage audit **inside** the eval
workbench on the latest agent snapshot.

Pair skill: `skills/loops_mcp/audit/SKILL.md` (outer loop via MCP).

---

## 1. What this loop does

For the latest snapshot, verify:

- **Distribution tags** — in-distribution, margin, and out-of-distribution cases
  sit in the correct region relative to the stated domain.
- **Problem-type tags** — client, technical, and adversarial problems are covered
  in the right proportions.
- **Safeguards** — concerns mapped in the governance profile have registry tags,
  and tagged cases actually exercise them.
- **Token cost** — average token cost per run across all cases.

Judgement logic follows `skills/governance_audit/SKILL.md`.

---

## 2. Run via API

```
POST /api/blueprints/run
Content-Type: application/json
```

The calling LLM may edit `instruction` and `tools` before posting:

```json
{
  "agent_name": "governance_auditor",
  "model": "gemini-2.5-flash",
  "instruction": "You are a governance auditor for an ADK agent snapshot.\n\nTools: get_governance, get_snapshot, list_cases, get_case, list_tags, list_scored_runs, run_report.\n\nDo the following until an audit report is complete:\n1. get_snapshot for the latest commit — read AgentDistribution and domain description\n2. list_cases — group by distribution tags (in/margin/ood) and problem-type tags (client/technical/adversarial)\n3. Flag cases that appear mis-tagged relative to the stated domain\n4. get_governance — for each NIST concern, check tags_present and cases_tagged; flag untested safeguards\n5. run_report or list_scored_runs — compute average token cost per run\n6. Write an audit report: distribution sanity, coverage gaps, safeguard gaps, cost summary\n\nExample sequence: get_snapshot → list_cases → get_governance → list_scored_runs → audit report.",
  "tools": [
    "get_snapshot",
    "list_snapshots",
    "list_cases",
    "get_case",
    "list_tags",
    "get_governance",
    "list_scored_runs",
    "run_report"
  ]
}
```

Fetch preset defaults from `GET /api/blueprints/presets` (`RegistryExplorer` is a
useful starting point for tag/case listing).

---

## 3. Stop condition ("until G")

**G** = a structured audit report covering all four areas (distribution,
problem-type coverage, safeguard testing, token cost) with explicit pass/flag
items and recommended follow-ups.

---

## 4. Caller responsibilities

- Point the blueprint at the correct `snapshot_id` (latest commit).
- Follow `skills/governance_audit/SKILL.md` for judgement criteria once available.
- This inner loop **reports** findings; remediation (new cases, tag fixes,
  governance updates) is a separate action or handled by the outer loop.
