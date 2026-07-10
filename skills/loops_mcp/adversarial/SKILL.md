# Skill: Adversarial Loop (outer — MCP)

Use this skill when **you** (the autonomous coding agent) own the adversarial
red-team loop: define attack modalities, create cases, fix the agent, verify.

Pair skill: `skills/loops_blueprint/adversarial/SKILL.md` (inner loop via API).

---

## 1. Connect to MCP

```bash
python run_app.py <repo> --mode mcp
```

Stdio server; repo path from `EVAL_WORKBENCH_REPO` (defaults to CWD).

---

## 2. What this loop does

1. Define adversariality modalities (tags).
2. Study the agent snapshot and craft attacks with your frontier reasoning.
3. Create adversarial cases and run them against the agent.
4. Hand failures to the harness optimisation loop — edit agent code, re-run,
   confirm the agent resists the attack class.

---

## 3. Tool sequence

**Recon and tag setup:**

```
1. get_snapshot         → agent tools, prompt, domain, distribution
2. list_tags            → existing adversarial tags
3. create_tag           → new modality tags if needed (repeat)
```

**Attack and case creation:**

```
4. generate_case        → adversarial scenario per modality (repeat)
   — or create_case with hand-crafted payload
5. list_cases           → confirm cases tagged adversarial
```

**Run and evaluate:**

```
6. generate_run         → run each adversarial case (repeat)
7. evaluate_run         → score (repeat)
8. list_scored_runs     → identify agent failures under attack
```

**Harness optimisation** (continue in this session or follow
`skills/loops_mcp/harness_optimisation/SKILL.md`):

```
9. get_case             → inspect each failure
10. [edit agent code — harden prompt, add safeguards, fix tool handling]
11. scan_agent → generate_run → evaluate_run → confirm attack blocked
```

---

## 4. Stop condition ("until G")

**G** = adversarial cases exist for each defined modality, the agent passes
re-run evaluation on those cases (or remaining failures have documented blurbs
and a planned fix iteration), and a red-team report summarises what was tested.

---

## 5. Where you act on results

| Phase | Action |
|---|---|
| Modality design | `create_tag` + document attack class in your notes. |
| Case creation | `generate_case` / `create_case` with adversarial tags. |
| Agent hardening | Edit agent source — you are the frontier attacker *and* the fixer. |
| Verify | Re-run adversarial suite after each hardening change. |
| Governance | Update `update_governance` if new safeguards were added. |

After the adversarial suite is green, run `skills/loops_mcp/ci_cd/SKILL.md` to
ensure no regression on the main dataset.
