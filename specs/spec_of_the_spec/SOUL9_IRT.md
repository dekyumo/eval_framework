Item Response Theory (IRT) is the statistical science of scoring test-takers from a finite bank of items. Map it directly:
- eval cases are items
- models/agents are test-takers
- the suite is the exam

The trap: a single agent evolving along a git line is not a population. If it fails A, B, C because they aren't built yet, IRT calls them "hard" — but that's a development-order artifact, not item difficulty. Difficulty is only identifiable across a population of test-takers.

So difficulty comes from a model campaign, not from one agent's history. Run the suite across a panel, weak models included:
- Gemini: flash-lite / flash / pro
- Claude: Haiku / Sonnet / Opus
- GPT: mini / normal / pro / o3

This is imperfect — prompts are optimised for a particular model — but within a family the weaknesses are largely shared, so the spread is still informative.

The object is the response matrix: (model x item) scores. Everything useful is an operation on it:
- difficulty: items only the strong models solve, partitioning the set into easy/medium/hard
- capacity: which family/size solves which problem, an input to model switching/routing
- correlation: which items fail together, a co-failure matrix

The co-failure matrix is phenomenological clustering (SOUL2) seen from the other side. SOUL2 clusters items by input content ("what is this eval about"); this clusters them by behaviour ("what skill does it exercise"). Items that always move together are one sub-skill, and one of each redundant pair can be dropped, which thins the test suite.

A priori difficulty is free and artifact-proof: the generation coordinates (domain in/margin/ood x problem happy/technical/adversarial/client) already rank intrinsic hardness before any model runs. The campaign calibrates that prior against reality.

=====================

In the evaluation framework:
- an eval campaign runs the suite across a fixed model panel
- store the (model x item) response matrix
- factor it for sub-skills, read difficulty from the strong/weak gradient, thin redundant items
- a single-agent run uses the generation coordinates as its difficulty prior
