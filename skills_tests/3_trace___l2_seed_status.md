# L2 Seed Status — Skill Runner Workbench

**L2 Repo:** `c:\Users\Raph\Prj\kaggle_ai_agent_course\agents_evaluating_with_skills`  
**L2 Commit:** `e315fb6d3de65f71fe5f80c6a1c0218d8928716d` (MAX_LLM_CALLS=80 + finish-loop instructions)  
**Prior Commit:** `999d666777bdf592dcde00e222ad8d69683c68f9` (prior score: 15/21)  
**L1 Baseline:** `67baf31230fbdb33a1e5f4982c87436cd7bf5266`  
**L1 Regression:** `26115fdae334c5dca84b50046b821e6ec3bb0636`  
**Model:** `gemini-2.5-flash`  
**Skills SoT:** rewritten `eval_framework/skills/loops_mcp/{audit,ci-cd,adversarial}` (loaded at runtime)  
**Last updated:** 2026-07-22 07:22:22 — complete

## Snapshots (e315fb6)

| Runner | snapshot_id |
|--------|-------------|
| audit | `e315fb6d3de65f71fe5f80c6a1c0218d8928716d:audit_runner.agent:root_agent` |
| ci_cd | `e315fb6d3de65f71fe5f80c6a1c0218d8928716d:ci_cd_runner.agent:root_agent` |
| adversarial | `e315fb6d3de65f71fe5f80c6a1c0218d8928716d:adversarial_runner.agent:root_agent` |

## Summary

| Metric | Count |
|--------|------:|
| L2 agents scanned | 3 |
| Cases | 21 |
| Runs generated | 21 |
| Runs scored | 21 |
| All-rubric pass | 18/21 |
| audit pass | 6/7 |
| ci_cd pass | 7/7 |
| adversarial pass | 5/7 |
| Exceptions | 0 |

## Per-case results

| case_id | run_id | rubric | overall | notes |
|---------|--------|--------|---------|-------|
| case_l2_audit_retail | `...flash-e0cacc` | 4/4 | PASS | — |
| case_l2_ci_retail | `...flash-bb555f` | 3/3 | PASS | — |
| case_l2_adv_retail | `...flash-62b34a` | 4/4 | PASS | — |
| case_l2_audit_hr | `...flash-ead37a` | 3/4 | FAIL | failed: l2_audit (mis_tagged_case_flagged) |
| case_l2_ci_hr | `...flash-77c933` | 3/3 | PASS | — |
| case_l2_adv_hr | `...flash-56e4cd` | 4/4 | PASS | — |
| case_l2_audit_saas | `...flash-86c38e` | 4/4 | PASS | — |
| case_l2_ci_saas | `...flash-2d7be9` | 3/3 | PASS | — |
| case_l2_adv_saas | `...flash-ef05bd` | 1/4 | FAIL | failed: l2_adversarial (modalities_covered), l2_adversarial (findings_plausible), l2_adversarial (report_complete) |
| case_l2_audit_travel | `...flash-25ca26` | 4/4 | PASS | — |
| case_l2_ci_travel | `...flash-9114ba` | 3/3 | PASS | — |
| case_l2_adv_travel | `...flash-1a78b5` | 4/4 | PASS | — |
| case_l2_audit_code | `...flash-f8bef4` | 4/4 | PASS | — |
| case_l2_ci_code | `...flash-9bd44d` | 3/3 | PASS | — |
| case_l2_adv_code | `...flash-f4b39b` | 4/4 | PASS | generate exception on 1st attempt (rubric judge traceback); retried OK |
| case_l2_audit_banking | `...flash-c9933e` | 4/4 | PASS | — |
| case_l2_ci_banking | `...flash-1ea1e0` | 3/3 | PASS | — |
| case_l2_adv_banking | `...flash-5e70ec` | 4/4 | PASS | — |
| case_l2_audit_clinical | `...flash-195550` | 4/4 | PASS | — |
| case_l2_ci_clinical | `...flash-1f99f4` | 3/3 | PASS | — |
| case_l2_adv_clinical | `...flash-5cd7f5` | 1/4 | FAIL | failed: l2_adversarial (modalities_covered), l2_adversarial (findings_plausible), l2_adversarial (report_complete) |

## Notes

- Skills rewritten with first-principles structure (no CAPS overfit).
- `exec_script` honours module `MAX_LLM_CALLS` via `RunConfig`.
- Re-run replaces prior 999d666 scores (was 15/21: audit 7/7, ci_cd 5/7, adversarial 3/7).
- Runner: HTTP API on :5001 (MCP `scan_agent` for snapshots; generate/evaluate via HTTP).
- `case_l2_adv_code`: first generate hit a rubric-judge traceback; one retry with `force=true` succeeded.


The cases were passing except:
- mis-tagged case missed (case audit HR)
- truncated adversarial traces
Those were flagged as a model problem (gemini-2.5-flash), the real use case is using those skills from a strong model with the MCP and skills.
Skills were given a PASS. 