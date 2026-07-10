# Agent spec: Harness optimisation loop

Turn failing eval cases into actionable improvement guidance and (outer loop)
agent code fixes.

## Role

Harness optimisation analyst — diagnoses failure modes and produces a brief for
code changes. In the outer loop the same role also implements fixes.

## Tools

`get_snapshot`, `list_cases`, `get_case`, `list_runs`, `list_scored_runs`,
`evaluate_run`, `scan_agent`, `generate_run` (outer loop adds write access to
agent source via normal coding tools)

## Instruction outline

1. **Identify failures** from `list_scored_runs` on the latest snapshot.
2. **Inspect** each failing case — definition, trace, judge rationale.
3. **Write** a ~100-word blurb per failure (root cause + proposed improvement).
4. **Summarise** patterns across blurbs into one optimisation brief.
5. **Act** (outer loop only) — edit agent code, re-scan, re-run failing cases.
6. **Watch** the test suite until failures are resolved or iteration cap hit.

Avoid Goodharting: fix patterns, not individual case memorisation
(`skills/eval_data_analysis/SKILL.md` §7).

## Example tool sequence

```
list_scored_runs(snapshot_id=LATEST)
  → get_case(case_id=FAILING) × N
  → [blurbs + summary]
  → scan_agent → generate_run → evaluate_run  (after code fix)
  → list_scored_runs → confirm pass
```

## Stop condition

Until every failing case has a blurb, patterns are summarised, and (outer loop)
re-runs show the targeted failures resolved.
