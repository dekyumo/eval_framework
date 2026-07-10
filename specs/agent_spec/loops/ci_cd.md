# Agent spec: CI/CD loop

Monitor a new commit against a baseline: scan, run cases, score, export CSV,
compare snapshots, greenlight or block.

## Role

CI/CD monitor — validates that a new agent commit does not regress the
regression dataset before merge.

## Tools

`scan_agent`, `get_snapshot`, `list_snapshots`, `list_cases`, `generate_run`,
`list_runs`, `evaluate_run`, `list_scored_runs`, `run_report`, `compare_snapshots`

## Instruction outline

1. **Scan** the agent at the target commit (`scan_agent`).
2. **Run** each case in the regression dataset (`generate_run`).
3. **Score** each run (`evaluate_run`).
4. **Export** results to CSV (`run_report`).
5. **Compare** the new snapshot to the previous commit (`compare_snapshots`).
6. **Decide** greenlight (no material regressions) or block (with cited cases).

Apply `skills/eval_data_analysis/SKILL.md` when reading the CSV and comparison
output. Inspect individual traces for any regressed case.

## Example tool sequence

```
scan_agent(commit=HEAD)
  → generate_run(case_id=…) × N
  → evaluate_run(run_id=…) × N
  → run_report(snapshot_id=…, dataset=…)
  → compare_snapshots(snapshot_a=BASE, snapshot_b=NEW)
  → verdict: greenlight | block
```

## Stop condition

Until a greenlight/block verdict is written with evidence from
`compare_snapshots` and per-case inspection of regressions.
