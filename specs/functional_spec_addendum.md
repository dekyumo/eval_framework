# Agent Evaluation and Provenance Workbench — Spec Additions

## 1. Evaluation Philosophy

### 1.1 Scientific Soundness

Evaluation design must consider:

* distributional coverage
* representative sampling
* boundary conditions
* uncertainty regions
* adversarial conditions
* evaluation cost

The objective is not to maximize test count, but to maximize information gained per evaluation.

---

## 2. Agent Contract / Agent Specification

### 2.1 AGENT_SPEC.md

Each agent must contain an explicit specification file:

```text
AGENT_SPEC.md
```

The specification describes:

* purpose
* intended users
* capabilities
* non-capabilities
* expected inputs
* expected outputs
* constraints
* risk boundaries
* allowed autonomy
* external effects

Example:

```text
Purpose:
  Assist customers with refund questions.

Capabilities:
  - explain refund policy
  - retrieve order status

Forbidden:
  - issue refunds
  - access payment credentials
```

---

### 2.2 Automatic Agent Specification Generation

If no specification exists, the system generates a draft specification from:

* agent topology
* prompts
* tools
* models

The generated specification is presented for human confirmation. In practice, this means a popup such as:

```text
AGENT_SPEC.md generated, please review
```

---

### 2.3 Specification Validation

A high-capability evaluator model compares:

```text
AGENT_SPEC.md
        |
        v
Implemented Agent
```

This process crawls the agent AST to inspect tool definitions, prompts, and related implementation details.

The evaluator then asks the LLM to check the agent specification and the implementation point by point.

This returns structured output using the pinned `Score` type (functional spec §11.3):

* `spec_item`
* `score` — float in `[0, 100]`
* `confidence` — `low` / `medium` / `high`
* `rationale`

It also returns specification indetermination points, such as:

* “is this ok?”
* “was this included?”
* “is that weird stuff in scope?”

---

# 3. Domain Modeling

From the agent spec, we can derive the shape of the domain: what requests the agent is supposed to see.

## 3.1 Domain Classification

The system derives three regions:

## In-domain

Tasks the agent is expected to handle.

Example:

```text
"Where is my refund?"
```

---

## Out-of-domain

Tasks outside the agent’s intended responsibility.

Example:

```text
"Explain quantum physics"
```

Expected behavior:

* refusal
* redirection
* clarification

---

## Boundary / Margin Cases

Cases close to the agent’s responsibility boundary.

Examples:

```text
Customer:
"The product didn't work, I might want a refund,
but actually I need a recommendation for another brand."
```

These test:

* intent resolution
* ambiguity handling
* scope control
* clarification behavior

---

# 4. Evaluation Case Generation

## 4.1 Generation Dimensions

Evaluation cases are generated from:

```text
domain position
+
problem type
```

Domain position:

* in-domain
* margin
* out-of-domain

Problem type:

* happy path (no problem)
* technical failure (LLM 503/429, garbage tool output, exception in tools)
* adversarial input (prompt injection, request for credentials, PII in input)
* client/user problem (confused, emotional, multiple requests in one)

---

## 4.2 Example Generation Matrix

Domain position is a single choice (radio) **per intent**: in-domain, margin, or out-of-domain.

A confused user who sends several intents in one turn is modeled not by turning the radio into a checkbox, but by letting a case carry **multiple intents**, each with its own domain radio. So "3 in-domain intents" or "one in-domain, one out-of-domain" is expressed as multiple intent rows, each cleanly single-choice. A normal case is just one intent row.

The user then selects one of the problem types from Section 6.

The framework generates an evaluation case that can then be modified by the user.

---

# 5. Evaluation Tags

All evaluation cases support tags.

Examples:

```text
smoke
regression
release
security
pii
robustness
resilience
llm_unavailable
tool_failure
ood
margin
domain
expensive
llm_judge
human_review
```

Tags let developers group evaluations by speed and cost, with the cheapest tests running on commits, more expensive tests on pull requests, and the most expensive tests on release.

They also let developers understand what kinds of tests exist in the system, including counts by tag and counts by tag pair.

Tags are closed categories:

* they must be defined in advance
* each tag has an assigned color
* tags cannot be deleted unless their count is 0
* tags can be renamed

This is intended to prevent the “mistyped tag meant a missing test” problem.

---

# 6. Robustness and Resilience Evaluation

Evaluation cases include controlled failures:

These are implemented with the MOCK / FAULT tool sandbox (functional spec §5.2): bad mock tools for data-quality faults, and HTTP errors on the LLM call for transport faults. There is no separate fault engine.

## Dependency failures

Examples (LLM transport faults, injected as HTTP errors on the model call):

* model unavailable (503)
* timeout
* rate limiting (429)
* service errors

Expected behavior:

* retry
* recover
* escalate
* avoid hallucination

---

## Data quality failures

Examples:

Malformed tool output:

```text
get_contract()

returns:

"meow meow rawr grrr"
```

Evaluate:

* validation
* uncertainty handling
* safe fallback

---

## Input robustness

Examples:

* noisy user messages
* incomplete requests
* emotional requests
* contradictory requests

---

## Adversarial robustness

Examples:

* instruction injection
* privilege escalation
* sensitive data exposure
* malicious requests

---

Tiers are just groups of tags. A "tier" (e.g. commit / PR / release) is selected by choosing which tags to run; there is no separate policy engine.
