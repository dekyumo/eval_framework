# Skill: Audit Loop (outer — MCP)

Use this skill when **you** (the autonomous coding agent) own the governance
audit loop. Drive the eval workbench MCP server directly.

Pair skill: `skills/loops_blueprint/audit/SKILL.md` (inner loop via API).

---

## 1. Connect to MCP

```bash
python run_app.py <repo> --mode mcp
```

Stdio server; repo path is the positional argument to `run_app.py`.

---

## 2. What this loop does

Audit the latest agent snapshot:

- Distribution tags (in / margin / ood) match the stated domain.
- Problem-type tags (client / technical / adversarial) are appropriately placed.
- **NIST AI RMF profile** — each snapshot carries a human-editable governance
  profile; verify concern-to-tag mappings and business justification.
- Average token cost per run is computed and compared to the business case.

---

## 3. NIST AI RMF profile (per snapshot)

Every scanned agent snapshot can have a **NIST AI RMF profile** persisted on it
(same persistence model as `AgentDistribution` — edited on the Agents page or via
MCP).

```python
governance = get_governance(snapshot_id)
# → concern_coverage, business_case, all_tags
```

| Field | Purpose |
|---|---|
| `concern_coverage` | Freeform prose: which NIST concerns (Govern / Map / Measure / Manage) map to which tags or case patterns |
| `business_case` | Business justification — scope, unit economics, MAP-3 style cost claims |
| `all_tags` | Registry tags returned alongside the profile for cross-check |

Also available on `get_snapshot` as `snapshot["governance"]` when set.

### Audit `concern_coverage`

Read the prose as **claims**, not structured data. For each stated mapping:

- Extract mentioned tag names or patterns (e.g. `legal`, `team_*`).
- Verify tags exist in `all_tags` / `list_tags`.
- Count cases carrying those tags via `list_cases`.
- Check the cited NIST concern is plausible for this agent's domain
  (`snapshot.distribution`).

Flag:

- **Broken references** — tag named in text but absent from the registry.
- **Untested claims** — tag exists but no cases carry it.
- **Missing concerns** — domain implies compliance, privacy, adversarial testing,
  etc., but the profile is silent or empty.
- **Implausible mappings** — tag does not match the concern described.

### Audit `business_case`

Read against token counts, pass rates, and unit economics:

- Estimate cost per run from `list_scored_runs` trace token fields or `run_report`.
- Check stated close rates against bool rubric aggregates.
- Flag vague claims when numbers are required for compliance.

### Remediation

- `update_governance(snapshot_id, { concern_coverage, business_case })` — revise
  profile text after human review.
- Do **not** auto-approve governance — surface flags and let a human confirm
  before bulk tag or governance edits.

---

## 4. Tool sequence

```
1. list_snapshots       → latest snapshot_id
2. get_snapshot         → AgentDistribution, domain description, governance blob
3. get_governance       → concern_coverage, business_case, all_tags
4. list_tags            → registry tags for cross-reference
5. list_cases           → all cases with tag assignments
6. get_case             → drill into suspicious cases (repeat)
7. list_scored_runs     → token/cost fields per run
8. run_report           → optional full CSV if scored runs are stale
```

Group cases by distribution and problem-type tags. Parse `concern_coverage`
freeform text and cross-check tag names against `list_tags` and case tag
assignments.

---

## 5. Stop condition ("until G")

**G** = audit report written with:

| Area | Output |
|---|---|
| Distribution | pass/flag per mis-tagged case |
| Problem types | coverage gaps listed |
| NIST safeguards | untested concerns / broken tag refs flagged |
| Token cost | mean cost/run + comparison to business case |

---

## 6. Where you act on results

| Finding | Action |
|---|---|
| Mis-tagged cases | Edit case tags or move cases; use `create_case` / registry tools if creating replacements. |
| Untested safeguard | Create cases tagged for that concern (`generate_case`, `create_case`). |
| Stale governance | `update_governance` to fix tag mappings or business justification. |
| High token cost | Report to user; cost fixes are agent-code changes (outside this loop). |
