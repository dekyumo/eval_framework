---
name: audit
description: >-
  Governance and coverage audit for an ADK agent snapshot via eval-workbench MCP:
  concern-tag semantics, distribution hygiene, NIST AI RMF concern_coverage vs
  cases, and business_case vs token cost. Use when asked to audit a snapshot or
  check governance completeness.
---

# Skill: Audit Loop (outer — MCP)

Drive the eval-workbench MCP server when you own the governance audit loop.

Pair skill: `skills/loops_blueprint/audit/SKILL.md` (inner loop via API).

---

## Purpose (first principles)

An audit answers one question: **does the eval set honestly represent what the
governance profile claims?** A good outcome is a structured report that separates
concern-tag correctness from distribution hygiene, cites specific case ids, and
flags both overstated coverage and silent gaps — without inventing problems the
dataset was not designed to test.

---

## Scope

**In scope**

- The snapshot under review and cases in its dataset(s)
- `concern_coverage` prose as testable claims
- `business_case` prose against measured token cost and pass rates
- Per-case distribution (`in` / `margin` / `ood`) and problem-type labels
- Concern tags on cases (semantic fit, not just presence)

**Out of scope**

- Fixing agent source code (hand off to harness optimisation)
- Cross-agent registry totals — count only cases belonging to this snapshot's eval set
- Approving or rewriting governance without a human in the loop

---

## Preconditions / IDs

**MCP connection**

```bash
python run_app.py <repo> --mode mcp
```

Stdio server; repo path is the positional argument. See `skills/eval_framework_mcp/SKILL.md`
for client setup.

**Snapshot id** — full string, not a commit hash alone:

```
{commit_hash}:{agent_python_path}:{python_var_name}
```

Example: `c97928…:a_single_agent.day_trip:root_agent`

Resolve via `list_snapshots` or the id provided in the task. Use the same id for
`get_snapshot`, `get_governance`, and scored-run queries.

**Governance fields** (`get_governance` or `snapshot["governance"]`):

| Field | Role |
|---|---|
| `concern_coverage` | Freeform claims mapping NIST concerns to tags or case patterns |
| `business_case` | Unit-economics and scope justification |
| `all_tags` | Tags returned with the profile for cross-check |

---

## Workflow

### Phase 1 — Orient

```
get_snapshot(snapshot_id)
get_governance(snapshot_id)
list_tags()
list_cases()          # filter to this snapshot's dataset(s)
list_scored_runs()    # or run_report if scores are stale
```

From `get_snapshot`, note: domain description, `AgentDistribution`, dataset
membership, and governance blob.

**Dataset scoping checklist**

- [ ] Identify which dataset(s) belong to this agent's eval programme
- [ ] Restrict all case counts and tag tallies to those datasets
- [ ] Do not cite cases from other agents or unrelated suites

### Phase 2 — Concern taxonomy pass

Read `concern_coverage` as **claims**, not structured data. Work through three
layers in order — do not substitute distribution complaints for concern findings.

**Layer A — Claimed concerns**

Extract every concern the prose explicitly maps to a tag or case pattern.

**Layer B — Concern checklist (domain scan)**

Walk the standard concern families and note which are claimed, which have cases,
and which the domain plausibly needs but the profile is silent on:

| Concern family | Example tags |
|---|---|
| Privacy / data minimisation | `privacy` |
| Safety / harm refusal | `harmlessness` |
| Fairness / disparate treatment | `biasedness` |
| Legal / regulatory | `legal`, `compliance` |
| Operational / fraud / abuse | `operational_risk` |
| Resilience / failure handling | `resilience` |

A concern is **missing** when the domain clearly needs it and the profile neither
claims it nor provides tagged cases.

**Layer C — Deferred coverage**

When prose defers a concern ("owned by ops", "out of band", "not in this eval"):

- [ ] Treat it as **untested**, not covered
- [ ] Record the deferral quote in the report
- [ ] Do not mark the concern green because someone else owns it elsewhere

### Phase 3 — Semantic review of concern-tagged cases

For every case carrying a concern tag (from Layer A or the checklist), call
`get_case(case_id)` and judge whether the scenario **actually exercises** that
concern.

Per case, record:

| Check | Question |
|---|---|
| Tag fit | Does the user turn match the concern label? |
| Governance alignment | Does `concern_coverage` cite this tag for this concern? |
| Verdict | `appropriate` / `mis-tagged` / `off-concern` |

A case tagged `privacy` that is really a tone check is a **concern mis-tag**, not a
distribution issue. A case tagged `in` that should be `ood` is **distribution
hygiene** — track it in a separate section.

**Minimum drill-down rule:** every concern tag with at least one case gets at
least one `get_case` review. Do not flag mis-tags from `list_cases` metadata alone.

### Phase 4 — Distribution and problem-type hygiene

Separate section from concern semantics:

- [ ] Group cases by `distribution_position` (`in` / `margin` / `ood`)
- [ ] Compare placement to `AgentDistribution` and domain description
- [ ] Group by `problem_type` (`client` / `technical` / `adversarial` / `happy`)
- [ ] Note proportion gaps — missing adversarial coverage, thin margin band, etc.

### Phase 5 — Business case vs measurements

- [ ] Estimate mean tokens per run from `list_scored_runs` or `run_report`
- [ ] Compare to cost claims in `business_case`
- [ ] Cross-check stated pass/close rates against bool rubric aggregates
- [ ] Flag vague economics when the profile asserts specific numbers

### Phase 6 — Write the report

Use the report shape below. Every flagged item needs a `case_*` id or an explicit
"no cases" note for a missing concern.

---

## Stop condition

**Done** when the audit report is written with all required sections and at least
one `get_case` review per concern tag present in the scoped dataset.

Partial data is acceptable — note what you could not verify and why. Do not
auto-approve governance; surface flags for human confirmation before bulk edits.

---

## Report shape

```markdown
## Audit report — {snapshot_id}

### Scope
- Dataset(s): …
- Cases reviewed: N

### Concern coverage
| Concern | Claimed in prose | Tags cited | Cases with tag | Semantic review | Status |
|---|---|---|---|---|---|
| privacy | yes | privacy | 3 | case_x appropriate, case_y mis-tagged | flag |

**Missing concerns:** …
**Deferred (untested):** …

### Concern mis-tags
| case_id | tag | issue |
|---|---|---|
| case_foo | compliance | scenario is fraud refusal, not policy compliance |

### Distribution hygiene
| case_id | current | expected | note |
|---|---|---|---|

### Problem-type coverage
…

### Business case
- Mean tokens/run: …
- Claim vs measured: …

### Recommended follow-ups
…
```

---

## Acting on results

| Finding | Action |
|---|---|
| Concern mis-tag on a case | Edit case tags; re-run audit on affected cases |
| Missing concern (no tag, no cases) | `create_case` / `generate_case` with appropriate concern tag; update `concern_coverage` |
| Untested claimed tag | Add cases or revise governance prose |
| Deferred coverage accepted by stakeholder | Document in `update_governance`; still list as untested in eval |
| Broken tag reference in prose | `update_governance` to fix mapping |
| Distribution mis-placement | Edit `distribution_position` on the case |
| High token cost vs business case | Report to user; agent-code changes are outside this loop |
| Stale governance narrative | `update_governance(snapshot_id, { concern_coverage, business_case })` after human review |
