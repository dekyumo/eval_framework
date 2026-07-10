# Skill: Governance Audit

Use this skill when reviewing an agent snapshot's **NIST AI RMF profile**. The
workbench stores two freeform fields; **you** read them, cross-check against tags,
cases, and runs, and judge whether the profile is credible.

---

## 1. Gather inputs

```python
governance = mcp_client.call("get_governance", {"snapshot_id": snapshot_id})
snapshot = mcp_client.call("get_snapshot", {"snapshot_id": snapshot_id})
cases = mcp_client.call("list_cases", {})
tags = mcp_client.call("list_tags", {})
```

| field | notes |
|---|---|
| `concern_coverage` | freeform text: which NIST concerns map to which tags / case patterns |
| `business_case` | freeform business justification (MAP-3 scope/costs) |
| `all_tags` | registry tags for cross-check |

Also pull scored runs or a benchmark report when auditing costs:

```python
report = mcp_client.call(
    "run_report",
    {
        "agent_path": snapshot["agent_target"]["agent_path"],
        "commit": snapshot["commit_hash"],
        "dataset_name": "<dataset>",
        "output_format": "csv",
    },
)
```

---

## 2. Audit `concern_coverage`

Read the prose as claims, not structured data. For each stated mapping:

- Extract mentioned tag names or patterns (e.g. `'legal'`, `'team_*'`).
- Verify tags exist in `all_tags` / `list_tags`.
- Count cases carrying those tags via `list_cases`.
- Check the NIST concern cited (Govern/Map/Measure/Manage subcategories) is
  plausible for this agent's domain (`snapshot.distribution`).

Flag:

- **Broken references** — tag named in the text but absent from the registry.
- **Untested claims** — tag exists but no cases carry it.
- **Missing concerns** — agent domain implies compliance, privacy, adversarial
  testing, etc., but the text is silent.
- **Implausible mappings** — tag does not match the concern described.

---

## 3. Audit `business_case`

Read against token counts, pass rates, and unit economics:

- Estimate cost per run from traces or `run_report` output.
- Check stated close rates against bool rubric aggregates.
- Flag vague claims when numbers are required for compliance.

---

## 4. Output format

Short audit memo:

1. **Concern coverage** — credible / gaps / broken tag references.
2. **Business case** — plausible / needs revision.
3. **Recommended actions** — create tags, add cases, revise profile text.
