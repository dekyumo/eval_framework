# Contract: NIST AI RMF profile on the agent snapshot

Implements issues/nist_ai_rmf_profile_on_agent_snapshot.md and
specs/spec_of_the_spec/SOUL7_GOVERNANCE.md.

## Principle

The snapshot area gains a human-curated **NIST AI RMF profile** (the standard
NIST term for documenting how an AI system applies the Risk Management
Framework). The platform does *not* try to be clever about NIST on its own; it
stores the profile and surfaces raw signals (which concern maps to which tag,
whether cases carry those tags). The actual judgement — "is this the right set
of concerns, is each one really tested, is the business justification
reasonable?" — is a **governance audit SKILL** run by an LLM. This mirrors
SOUL7's closing note: governance influences *usage* of the platform more than
the platform's own logic.
Scope is deliberately minimal: two UI panels plus the data behind them.

## Domain (already stubbed)

`domain/governance.py`:
- `NIST_CONCERN_CATEGORIES: list[str]` — the canonical concern list.
- `ConcernCoverage { category, tag_ids, note }`.
- `GovernanceProfile { business_case: str, coverage: list[ConcernCoverage] }`.

`GovernanceProfile` is attached to `AgentSnapshot.governance` and persisted by
`SnapshotRepository` on the `Snapshot.governance` JSON column — **the same
mechanism as `AgentDistribution`**. No separate store. This intentionally shares
the re-scan limitation documented in
issues/rescan_persistence_two_scan_modes.md; do not work around it.

## Service (`services/governance.py`)

- `get_governance(repo_path, snapshot_id) -> dict`
  - 404 (ServiceError) if the snapshot is missing.
  - Returns `business_case`, the canonical `categories`, the stored `coverage`
    normalised to one entry per category (missing categories filled with empty
    defaults), and `all_tags` (registry tags) for the UI mapper.
  - For each coverage entry, compute two derived signals so the UI needs no
    extra calls:
    - `tags_present`: every `tag_id` resolves to a registry Tag.
    - `cases_tagged`: count of `EvalCase`s carrying at least one mapped tag.
- `update_governance(repo_path, snapshot_id, data) -> dict`
  - Loads the snapshot, sets `governance = GovernanceProfile(...)`, saves via
    `SnapshotRepository`, returns the refreshed `get_governance` view.
  - 404 if the snapshot is missing.

Follow the AGENTS.md rule: let errors propagate as `ServiceError`; no silent
fallbacks.

## Routes (already wired, thin)

`web/routes/governance.py`, prefix `/api/governance`:
- `GET  /api/governance/<snapshot_id>`
- `POST /api/governance/<snapshot_id>`  (body: `{business_case, coverage}`)

## Frontend (Agents page)

Add two minimal panels below the existing "Distribution Definition" pane on
`pages/Agents.tsx`, loaded from `/api/governance/<snapshot_id>` when a snapshot
is selected, saved via POST:

1. **Concern coverage** — "what tags check what issues". A row per
   `NIST_CONCERN_CATEGORIES` entry: the category label, a multi-select / text
   mapping of registry tags, an optional note, and a read-only badge showing
   `tags_present` and `cases_tagged`. This lets a human answer *are the tags
   present, do those tags test that aspect, is the concern list appropriate?*
2. **Business justification** — a single textarea for the economic rationale
   (MAP-3 scope and costs: "doing it with people costs $X, with the agent $Y at
   close-rate Z…").
Keep styling consistent with the existing panes (`PagePane`, `TextAreaWithLabel`,
`Button variant="cta"`). A single "Save Governance" button POSTs both panels.

## Governance audit SKILL

Create `skills/governance_audit/SKILL.md` (external skill, same audience as
`skills/eval_data_analysis`). It instructs an LLM to, given a snapshot's
governance view + tags + cases + token/cost data:
- sanity-check that the concern list is appropriate (flag missing or unnecessary
  concerns for the agent's domain);
- verify each mapped concern is actually exercised by tagged cases;
- assess whether the business justification is reasonable against real token counts
  and common-sense unit economics.

The skill is the "intelligence"; the backend only serves the raw signals.

## Tests

`tests/test_governance.py`: round-trip `update_governance` → `get_governance`,
404 on unknown snapshot, and `cases_tagged` / `tags_present` computation against
a seeded snapshot + tags + cases (see tests/conftest.py fixtures).

Add one e2e step in `frontend/tests/e2e.spec.ts`: select a snapshot, fill the
business case, save, reload, assert it persisted.
