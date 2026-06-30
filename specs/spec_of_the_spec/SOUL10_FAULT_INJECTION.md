Hey, fault injection won the previous agentic hackathon. I don't know anything about it, so I asked an LLM to explain it to me in this file.


Fault injection is a real engineering discipline, older than LLMs, born in hardware dependability and distributed systems. The premise is simple: a system that is never stressed has never been tested, only used. So you deliberately introduce faults and watch what happens. For an agent, the faults are misbehaving tools and misbehaving model calls, and the question is whether the agent bends, breaks, or lies.

The fault -> error -> failure chain
-----------------------------------

The foundational vocabulary comes from the dependability taxonomy (Avizienis, Laprie, Randell, Landwehr). Three distinct things, often confused:

- fault: the cause. A tool returns garbage, the model endpoint throws a 503.
- error: the latent bad state inside the system. The agent has now incorporated the garbage into its reasoning, but nothing visible has happened yet.
- failure: the observable deviation from correct behaviour. The agent confidently tells the customer something false.

The whole point of robustness testing is to inject a fault and see whether it is contained (stays a fault), propagates (becomes an error), or escapes (becomes a failure). A good agent turns faults into safe non-events. A bad one turns a single bad tool call into a confident wrong answer to a human. The chain is the thing we are measuring along.

Fault models: a taxonomy of how things break
--------------------------------------------

Distributed systems classified faults long ago, from mildest to nastiest. Each maps cleanly onto an agent's dependencies:

- crash / fail-stop: the component just stops. A tool raises an exception, the model call dies.
- omission: the component silently drops the response. No return value, a hang, a timeout.
- timing: the response is correct but too slow (or too early). Latency faults, the model takes 40s.
- value / response faults: the component returns the wrong thing. A tool returns a plausible-but-wrong number, or `meow meow grrr`.
- Byzantine / arbitrary: the worst class. The component behaves inconsistently, maliciously, or self-contradictorily. Malformed payloads, schema violations, a tool that lies differently each call, prompt injection arriving through tool output.

Value faults and Byzantine faults are the interesting ones for agents, because an LLM is a credulous component: it will often rationalise garbage rather than reject it. Crash and timing faults are easy by comparison, they usually just need a retry.

FARM: the structure of a fault injection experiment
---------------------------------------------------

The classic experimental model (Arlat et al., LAAS) is FARM. It happens to be exactly the shape of an eval:

- F (Faults): the set of faults injected. The fault model plus where and when.
- A (Activation): the workload that exercises the system so the fault can matter. This is the eval case / conversation.
- R (Readouts): what we observe. The trace.
- M (Measures): what we derive. The robustness / resilience score.

So a fault-injection eval is just `F x A -> R -> M`. The framework already has all four: FAULT config, eval case, trace, score. Naming FARM mostly tells you the dimensions you must vary deliberately: it is not enough to pick a fault, you must also pick the activation that makes it bite, and decide in advance what readout proves the agent handled it.

=====================

Where to inject: the fault space of an agent
--------------------------------------------

A fault is defined by a location, a type, a trigger, and a duration. The injection points in an agent are its boundaries:

- user input boundary: noise, incompleteness, contradiction, emotion, prompt injection, PII.
- tool-call boundary: the agent calls a tool with bad arguments (test the tool's own guards), or the call itself fails.
- tool-result boundary: the tool returns crash / omission / timing / value / Byzantine output. This is the richest point.
- model transport boundary: the HTTP call to the model returns 429, 503, timeout, malformed stream.
- model output: the model returns refusals, truncations, format violations (a fault the agent must survive even though it is "internal").
- state / memory: corrupted or stale context, dropped history (relevant once agents have memory).
- inter-agent boundary: in a multi-agent topology, one sub-agent feeds another a faulty message. Faults cascade.

Triggers matter: a fault on the first tool call tests early detection; a fault on the third call after two good ones tests whether the agent was lulled. Duration matters: a transient 503 (recover by retry) is a different test than a persistent one (recover by escalation).

Robustness vs resilience: two different measures
------------------------------------------------

The words are not synonyms, and the framework should score them separately:

- robustness: does the agent stay correct (or safely refuse) while the fault is present? Graceful degradation. Bending without breaking.
- resilience: does the agent recover and return to normal after the fault? Retry, escalate, self-heal. Bouncing back.

Under a fault, the behaviours worth scoring are: detect (notice something is wrong), contain (do not propagate the bad value into the answer), recover (retry / fall back / escalate), and the failure mode to punish hardest, confabulate (paper over the fault with a confident invented answer). Detect-and-escalate beats silent-success-by-luck.

The oracle problem
------------------

When you inject a fault, what is the correct behaviour? Usually there is no single ground truth. "The contract tool returned gibberish" has no numeric right answer; the right answer is a behaviour ("do not trust it, ask, or escalate"). So most fault-injection evals are rubric / judge evals, not deterministic verifiers. The rubric axes are the behaviours above: detection, containment, recovery, honesty. A few faults do have deterministic oracles (a 503 should produce a retry that appears in the trace), and those are cheaper, prefer them where they exist.

Which faults to inject: you cannot inject everything
----------------------------------------------------

The fault space is combinatorial, so reliability engineering prioritises. Two tools worth borrowing:

- FMEA (failure modes and effects analysis): for each failure mode, score severity x likelihood x detectability. Inject the high-product ones first. A wrong refund amount (high severity) beats a slow weather lookup.
- fault tree analysis: start from a top-level bad outcome ("agent issues a refund it should not") and decompose deductively into the faults that could cause it. Inject the leaves.

This keeps the FAULT suite small and meaningful rather than a random pile of broken mocks. It also gives coverage a definition: you have coverage when each high-priority fault class has been injected at each relevant boundary.

The production cousin: chaos engineering
----------------------------------------

Chaos engineering (Netflix's Chaos Monkey, the Principles of Chaos) is fault injection moved into production: define a steady-state hypothesis (what normal looks like), hypothesise it survives a fault, inject in prod with a minimised blast radius, measure the deviation. Modern distributed-systems testing (Jepsen) injects network partitions and value faults to find consistency bugs. This is out of scope here (we test before deployment, not in prod), but two ideas transfer: the steady-state hypothesis is a clean way to phrase the expected behaviour under fault, and "blast radius" is a reminder that LIVE faults must be sandboxed so a test cannot touch the real world.

Reproducibility of a fault
--------------------------

A fault is part of the experiment, so it must be deterministic and versioned: the same fault, same trigger, same seed, same result. The mock and fault code is stored and fingerprinted, exactly like a prompt. A non-deterministic fault would make a robustness regression impossible to attribute.

A speculative note
------------------

The optimistic end of this field is antifragility (Taleb): systems that get stronger from stress. For an agent, the loop is: a fault that produced a failure becomes a new permanent eval case, the agent is fixed, and the suite is now harder. Failures feed the test set. That is where fault injection meets the loops soul.

=====================

In the evaluation framework:

- FAULT is the MOCK machinery configured to misbehave, at a chosen boundary, with a chosen fault class, trigger, and duration.
- a fault-injection case is FARM: a fault config, an activating conversation, the resulting trace, a score.
- score robustness and resilience as separate rubric axes (detect / contain / recover / honesty), with deterministic oracles where a fault has an obvious correct response (a 503 should yield a visible retry).
- prioritise the FAULT suite with FMEA / fault-tree thinking; do not enumerate the whole fault space.
- faults are deterministic and fingerprinted, like prompts, so a robustness regression can be attributed.
- LIVE faults must be sandboxed; the blast radius of a test is the test environment, never the world.
