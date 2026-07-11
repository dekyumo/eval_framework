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
- **NIST AI RMF profile** — each snapshot has a governance profile
  (`concern_coverage` + `business_case`); verify concern-to-tag mappings and
  that safeguards are exercised by tagged cases.
- **Token cost** — average token cost per run across all cases, compared to the
  business justification.

---

## 2. NIST AI RMF profile (per snapshot)

Every agent snapshot can carry a **NIST AI RMF profile**, persisted on the
snapshot (editable on the Agents page, readable via `get_governance`).

```python
governance = get_governance(snapshot_id)
# → concern_coverage, business_case, all_tags
```

| Field | Purpose |
|---|---|
| `concern_coverage` | Freeform prose mapping NIST concerns to tags / case patterns |
| `business_case` | Business justification and unit-economics claims |
| `all_tags` | Registry tags for cross-check |

Also on `get_snapshot` as `snapshot["governance"]` when populated.

**Judgement criteria** (same as outer loop):

- Parse `concern_coverage` as claims; verify tag names exist, cases carry them,
  and concerns fit the agent domain.
- Parse `business_case` against `list_scored_runs` / `run_report` token costs
  and rubric pass rates.
- Flag empty profiles when the domain clearly needs governance coverage.

---

## 3. Run via API

```
POST /api/blueprints/run
Content-Type: application/json
```

The calling LLM may edit `instruction` and `tools` before posting:

```json
{
  "agent_name": "governance_auditor",
  "model": "gemini-2.5-flash",
  "instruction": "You are a governance auditor for an ADK agent snapshot.\n\nTools: get_governance, get_snapshot, list_cases, get_case, list_tags, list_scored_runs, run_report.\n\nDo the following until an audit report is complete:\n1. get_snapshot for the latest commit — read AgentDistribution, domain description, and governance profile if present\n2. get_governance — read concern_coverage (NIST concern → tag mappings) and business_case; cross-check all_tags against list_tags and case tag assignments\n3. list_cases — group by distribution (in/margin/ood) and problem-type (client/technical/adversarial); flag mis-tagged cases\n4. For each NIST concern stated in concern_coverage, verify tags exist and cases exercise them; flag untested safeguards\n5. list_scored_runs or run_report — compute average token cost per run; compare to business_case claims\n6. Write an audit report: distribution sanity, coverage gaps, NIST safeguard gaps, cost summary\n\nExample sequence: get_snapshot → get_governance → list_cases → list_scored_runs → audit report.",
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

## 4. Stop condition ("until G")

**G** = a structured audit report covering all four areas (distribution,
problem-type coverage, NIST safeguard testing, token cost) with explicit pass/flag
items and recommended follow-ups.

---

## 5. Caller responsibilities

- Point the blueprint at the correct `snapshot_id` (latest commit).
- This inner loop **reports** findings; remediation (new cases, tag fixes,
  `update_governance`) is a separate action or handled by the outer MCP loop.
