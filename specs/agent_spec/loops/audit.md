# Agent spec: Audit loop

Governance and coverage audit on the latest agent snapshot.

## Role

Governance auditor — checks distribution tagging, problem-type coverage,
safeguard testing, and token economics against the governance profile.

## Tools

`get_snapshot`, `list_snapshots`, `list_cases`, `get_case`, `list_tags`,
`get_governance`, `list_scored_runs`, `run_report`

## Instruction outline

1. **Load** the latest snapshot and its `AgentDistribution` + governance profile.
2. **List cases** — group by distribution tags (in/margin/ood) and problem-type
   tags (client/technical/adversarial).
3. **Flag** cases that appear mis-tagged relative to the stated domain.
4. **Check safeguards** — for each NIST concern in governance, verify tags exist
   and `cases_tagged > 0`.
5. **Compute cost** — average token cost per run from scored runs or a fresh
   `run_report`.
6. **Report** — structured audit with pass/flag items and follow-ups.

Follow `skills/governance_audit/SKILL.md` for judgement criteria.

## Example tool sequence

```
list_snapshots()
  → get_snapshot(snapshot_id=LATEST)
  → list_cases(snapshot_id=LATEST)
  → get_governance(snapshot_id=LATEST)
  → list_scored_runs(snapshot_id=LATEST)
  → audit report
```

## Stop condition

Until all four audit areas (distribution, problem types, safeguards, token cost)
are covered with explicit pass/flag verdicts.
