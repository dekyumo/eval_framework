# Agent Evaluation and Provenance Workbench

## 1. Overview

### 1.1 Problem Statement

Programming in ADK is relatively smooth, but evaluating agents is still awkward. In practice, it often requires manually assembling folders, duplicating YAML and JSON definitions, and wiring together CLI commands just to run a basic pre-test.

This project aims to make ADK agent evaluation reproducible, inspectable, and much less manual.

### 1.2 Goals

Provide a reasonable pre-testing framework for ADK agents in Python.

The system should help users:

* snapshot an ADK agent at a specific commit
* run evaluations against that snapshot
* compare agent versions
* track prompts, models, tools, and hierarchy changes
* support both automatic and human evaluation

### 1.3 Non-goals

This is not a production observability platform for agents.

It should not try to reimplement Braintrust, Arize, or a full tracing/monitoring stack. That would be scope creep and would pull the project away from its core purpose: reproducible evaluation before deployment.

### 1.4 Design Principles

* Reproducibility
* Agent-as-artifact
* Evaluation as a scientific process
* Separation from production observability
* Explicit versioning of models, prompts, tools, and code
* Prefer simple, inspectable representations over hidden magic

---

# 2. Core Concepts

## 2.1 Agent

An ADK agent in Python.

The whole ADK agent is considered part of the unit under test, including:

* tools
* skills
* pre-hooks
* subagents
* routing logic
* model configuration
* prompt/instruction content

The framework should treat the agent as a structured artifact, not just as a prompt string.

## 2.2 Agent Snapshot

An immutable representation of an agent at a point in time.

Contains:

* source commit (clean, no uncommitted modified files)
* dependency versions
* model identifiers
* sampling parameters (temperature, top-p, etc.) — these are part of the agent, not the run
* prompt versions
* tool configuration
* agent topology
* optionally, the commit of this evaluation framework itself, so the snapshot records the tooling that produced it

An agent snapshot is the unit that gets evaluated. Sampling parameters belong to the snapshot because they are a property of the agent's intended behavior (a creative agent runs hot, a routing agent runs cold).

## 2.3 Metrics

A metric is **one concept**: something attached to an evaluation case that points at a target ("the truth") and produces a score for a trace. What differs between metrics is only *how* the truth is established. There are three strategies:

* **Deterministic from the trace**

  * The value is extracted directly from the trace and compared to a stored ground truth.
  * Covers classification (including intent classification) and regression-style numerical tasks.
  * Verification is a parser / extraction function plus a comparison.
* **External verifier (RL-style)**

  * The truth is established by running an external function or program over the output.
  * Examples: logic proofs, theorem checks, code that must pass tests, formal validation.
  * The verifier returns `True` / `False` or a structured result, like a reward function.
* **Rubric only**

  * There is no extractable ground truth; the metric is a rubric judged by an LLM and/or a human on the same axes.
  * Examples: open-ended responses, creative tasks, ambiguous outputs.
  * Includes pairwise comparison (a rubric whose output is "which of two traces is better").

All three produce the same kind of result (see Score, §11.3), so they can be stored, compared, and aggregated uniformly. Some metrics imply an absolute ground truth; rubric-only metrics support relative ranking or rubric-based judgment.

## 2.4 Evaluation Run

An evaluation run is a single evaluation experiment.

Contains:

* agent snapshot
* the selected evaluation cases
* execution environment (the isolated worktree it ran in)
* results

A single run may execute each case several times. Repetitions are not averaged away: each repetition produces its own trace, and the set of repetitions becomes a small data series that feeds the scikit-learn metrics (e.g. mean and standard deviation of a score across runs).

An evaluation run should be reproducible whenever possible. The evaluator code itself is not separately versioned inside the run; if reproducibility of the tooling matters, pin the framework commit in the snapshot (§2.2).

## 2.5 Version Lineage

The various agent code versions are linked in a Git graph.

This means that it is not always useful to compare two distant versions directly if there are breaking commits in between. The more useful comparison is often the step-by-step difference between adjacent versions:

* A → B
* B → C
* C → D

This is standard breaking-change detection over Git history, and it should help the user understand what changed and what may have caused a regression.

Lineage is just the Git graph stored alongside the snapshots (§10.1). There is no separate "provenance engine"; the graph store answers lineage and comparison queries directly.

---

# 3. Agent Discovery

## 3.1 ADK Agent Loading

Input:

```text
repository/
  agent.py
```

Output:

An instantiated agent object.

The clean Git commit *is* the agent. Loading therefore works as a get-or-create against the agent's Kuzu database (one database per agent, §10):

* the repository must be on a clean commit (no uncommitted modified files); a dirty repository is rejected
* if a snapshot already exists for that commit, it is loaded from the database
* otherwise the agent is instantiated from source at that commit, scanned, and persisted as a new snapshot

Because identity is anchored to the commit, an unseen commit is unambiguously a new snapshot.

## 3.2 Agent Graph Extraction

Extract:

* agent hierarchy
* delegation relationships
* tools
* models
* prompts

The result is an agent manifest containing:

* name
* model
* prompt
* tools
* skills
* hooks

The system should also try to reconcile the loaded agent with existing prompts in the database. If a prompt already exists, it should be reused rather than duplicated.

## 3.3 Agent Identity

The identity of an agent is defined by:

* name
* versioned prompt
* Git commit
* full model name
* dependency snapshot

The main complication is agent renaming. A rename can break the graph even when the underlying agent is effectively the same.

This should be detected efficiently. A practical approach is to use an LLM-assisted comparison: if everything matches except the name, the system should prompt the user and suggest that the agent may have been renamed.

This implies that agent lineage should support soft links: two differently named agents can still be treated as the same logical agent by the framework if the evidence supports it.

---

# 4. Version and Change Tracking

## 4.1 Git Integration

Requirements:

* a commit is required to take an agent snapshot
* modified files should not be accepted as a final snapshot
* the Git commit is part of the agent definition
* branch metadata must be stored
* the commit graph must be available so agent lineage can be traced
* dirty repository detection is required

The goal is to make the snapshot fully anchored in version control.

## 4.2 Semantic Diff

Compare agent versions and detect changes in:

* prompt
* model
* tool set
* hierarchy
* loaded dependencies

This can be done efficiently by diffing the agent snapshot rather than trying to infer everything from runtime behavior.

The semantic diff should be able to answer questions like:

* What changed?
* Is this a rename or a new agent?
* Which subagent changed?
* Which tools were added or removed?
* Did the model version change?

---

# 5. Execution Environment

## 5.1 Agent Runner

Execute an agent against evaluation cases.

The runner should be able to:

* load a specific snapshot
* run inside an isolated Git worktree checked out at the snapshot's commit, so reruns of older versions and concurrent runs never corrupt each other's working tree or module state
* execute each case one or more times (repetitions produce a data series, §2.4)
* capture outputs and traces
* store the run for later comparison

### Run Isolation

Rerunning an older version means checking out its commit and reloading the module. Doing this in the main working tree is unsafe under concurrency. Instead, each run is performed in a throwaway Git worktree dedicated to that commit, with its own environment (a fresh virtual environment, e.g. `uv`), and removed afterwards.

This is the standard worktree-per-task isolation pattern. We drive `git worktree add` / `git worktree remove` directly (Python via subprocess or a small helper); existing tools such as `flywheel-worktree` are useful prior art but the orchestrators surveyed (hawt, wt, parsec) target interactive coding agents rather than an embedded eval runner, so we keep the dependency thin. Isolation here is about **correctness under concurrency**, not security sandboxing (see §11).

## 5.2 Tool Control

Tool behavior must be controlled to preserve reproducibility.

Supported modes:

* **LIVE**

  * Real tools run. Allowed only when explicitly declared (see §11.2).
* **MOCK**

  * Tools are replaced by mocks that return predefined outputs. Mocks can be generated automatically (an LLM inspects the tool to produce a mock that respects the expected schema) and are stored as inspectable code.
* **FAULT** (fault injection)

  * A mock that deliberately misbehaves, to test robustness. Two flavors:

    * bad tool output — a tool returns garbage (e.g. `meow meow grrr`), an exception, or a malformed payload
    * LLM transport errors — the model call returns HTTP errors such as `429` or `503`

The default should be to avoid uncontrolled external dependencies. Fault injection is the concrete mechanism behind the robustness/resilience cases described in the addendum: there is no separate "fault engine," it is just the MOCK machinery configured to fail.

---

# 6. Evaluation Framework

## 6.1 Evaluation Types

### Intent Classification

Used for routing and classification tasks.

Metrics:

* all classification metrics available in scikit-learn
* accuracy
* precision
* recall
* F1

This requires ground truth.

---

### Deterministic Verification

Used for:

* structured outputs
* mathematical answers
* extracted information
* mathematical proofs

Interface:

```text
verify(input, output)
```

The verifier may return:

* regression metrics for numerical values
* classification for true/false outputs
* classification for multiple-choice outputs

---

### Execution Verification

Used for:

* code

The output is checked by running an external verifier.

The result should include:

* True/False verification
* rubric-based quality signals when relevant

This category is especially important because correct output does not necessarily mean good output.

---

### Subjective Evaluation

Used for:

* open-ended responses
* creative tasks
* ambiguous outputs

Methods:

* LLM judge with rubrics
* agent as judge, including trace-based evaluation and VQA-style question answering
* human review using the same rubric as the LLM judge
* pairwise comparison

The system should support both scalar scores and structured comments.

---

# 7. Evaluation Dataset Management

## 7.1 Dataset Creation

Sources:

* manual creation
* generated cases (available from day one)
* copy of an existing case

Generation is a first-class, day-one feature, and deliberately simple: examine the agent (and its spec), guess the domain and its boundaries, then generate evaluation cases across domain position and problem type. It is a generation aid presented for editing, not a replacement for human review.

Copying is the simple alternative to automated mutation: any case can be duplicated into a new case which the user then tweaks. There is no automated mutation engine — a copy-and-edit operator covers the useful need without the complexity.

## 7.2 Dataset Diversity

Track:

* coverage
* difficulty
* categories
* edge cases

The dataset should be intentionally diverse rather than optimized for a single narrow behavior.

## 7.3 Human Annotation

Provide an interface for:

* labeling
* ground truth entry
* rubric-based scoring
* comments

Human labels should be stored in a reusable form so they can become part of the evaluation corpus.

---

# 8. Experiment Analysis

## 8.1 Run Comparison

Compare:

```text
Agent snapshot A
vs
Agent snapshot B
```

The comparison should show changes in:

* F1
* regression metrics
* rubric scores
* classification metrics
* pairwise judgments

For rubric-based metrics, the comparison should operate at the same level as the rubric items themselves. If a rubric item is a boolean, enum, or number, it should be compared directly.

Human/LLM agreement is reported per item by item type: boolean and enum items use a confusion (classification) table plus Cohen's kappa; numeric items use a correlation. Rank correlation alone is not used for boolean items, where it is degenerate.

The report has two levels rather than a full OLAP cube:

* a summary matrix of `tag × metric` showing the aggregate score (and delta A→B) per cell
* a per-cell drill-down: click a cell to get the underlying per-case table (case, score A, score B, delta), with the trace one click away

The UI should present agent snapshots in Git branch order as a directed graph. Any two snapshots can still be compared, but the graph should make lineage obvious.

The comparison view should work like this:

* show the directed graph of agents
* click two snapshots
* replace the bottom portion of the screen with the comparison view
* provide a way to return to the graph

## 8.2 Regression Detection

The system should show the change between two versions and highlight regressions.

It should also support rerunning older versions with newly added evaluations. This requires checking out the relevant branch or commit, reloading the module, and running the new evals against the old snapshot.

This is important because the evaluation suite may evolve over time, and older versions should be re-tested when new cases are added.

---

# 9. Web Interface

## 9.1 Agent Explorer

Visualize:

* agent graph
* tools
* models
* prompts

Agent snapshots, including names, prompts, and related metadata, should be stored as Markdown where appropriate so they can be rendered directly in the UI using a Markdown-to-HTML display component.

## 9.2 Evaluation Dashboard

Show:

* runs
* scores
* evaluation status
* per-case results

This view is primarily for inspecting a single evaluation or a small set of related evaluations.

## 9.3 Comparison

Compare two agent snapshots.

The comparison view should expose:

* structural differences
* metric differences
* evaluation failures
* provenance links back to the Git graph

---

# 10. Storage Architecture

Everything is stored in Kuzu, with **one database per agent**. The stores below are tables (node/edge tables) inside that single database, not separate systems. Evaluation data lives in its own tables in the same database.

## 10.1 Graph Store

Stores:

* Git graph

  * commit `on_top_of` parent commit
  * can be reset and reloaded from scratch
* agent topology

  * JSON representation of the agent snapshot
* prompt versions

  * prompt identity is derived by fingerprinting the ADK instruction template *before* `.format` is applied (ADK exposes the raw template), so two commits using the same template resolve to the same prompt identity regardless of runtime substitution
* mock tool identity

  * based on fingerprinted source code

The graph store supports lineage and comparison queries directly.

## 10.2 Eval Case Store

Stores:

* evaluation cases
* ground truths
* metric definitions
* rubric definitions

This is the canonical store for test cases.

## 10.3 Eval Run Store

Stores:

* the agent specification used for the run
* the evaluation case
* the raw output
* the structured output
* the Google GenAI-style message parts or equivalent trace representation
* an optional exception — a crash is not a special case, it is just a trace that carries an exception, which a metric can score like anything else

This is the record of what actually happened during execution.

## 10.4 Scored Eval Run Store

Stores:

* the evaluation run
* the computed metrics
* the final score(s)

This is the result of applying the evaluators to the raw run.

## 10.5 Human Eval Store

Stores cases that were evaluated by a human.

The human should be able to:

* fill in metric fields
* answer rubric items
* add comments

Human evaluation should be stored in the same general structure as automated evaluation so that the two can be compared.

---

# 11. Reproducibility

Reproducibility and security are different concerns; this section is about reproducibility and correctness, not about sandboxing untrusted code.

## 11.1 Model Pinning

Remove as much non-reproducibility as possible.

Model references must be fully qualified and versioned. Floating references such as `latest` should not be accepted for reproducible snapshots. Sampling parameters that affect behavior (temperature, etc.) are pinned in the snapshot (§2.2).

## 11.2 Tool Control

Require explicit declaration of external access.

Any tool that reaches outside the local evaluation environment must be declared, mocked, or explicitly approved (LIVE). The default is MOCK; FAULT is used for robustness cases (§5.2).

## 11.3 Score Type

A score is a single pinned type used everywhere a metric, rubric item, or audit item produces a value:

* `value`: float in `[0, 100]`
* `confidence`: one of `low` / `medium` / `high`

This applies uniformly to deterministic metrics, external verifiers, rubric items, and spec-audit items.

---

# 12. Future Extensions

Basic eval generation is a day-one feature (§7.1), not a future item. The future work is the *smarter* generation that proposes new cases based on:

* previous failures
* uncovered behaviors
* missing categories
* changes in agent structure

Also future:

* RAG / top-K retrieval evaluation (recall@k, MRR, etc.). Deferred because the right integration point for retrieval inside ADK is not yet settled.
