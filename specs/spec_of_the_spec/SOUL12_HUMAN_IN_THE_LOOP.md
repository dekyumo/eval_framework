An LLM has three weaknesses:

- no grounding. It has no source of truth except what you put in the context. Ask it to handle a ticket and it will cheerfully say "our automated calling system will send you the number" when there is no automated calling system. It is not lying; it has no way to check. Ungrounded confidence is the default failure mode (the confabulation axis of fault injection).
- no company. It does not know the firm it works for: the unwritten norms, the brand voice nobody documented, what the business actually values, which mistakes are fireable. That context lives in people.
- no taste. It has no stable preferences of its own. Hand it a rubric and it will agree with it; hand it the opposite and it will agree with that too. It is sycophantic by construction, so it cannot be the ground-truth source for a domain where truth is a matter of judgement.

So in an unverifiable domain the human is the anchor: the source of ground truth, the holder of taste, the one with eyes on the actual world. Everything the LLM judge produces is provisional until a human has calibrated it.

But human attention is the scarcest and most expensive thing in the system. You cannot have a person read every trace. So the platform is, in part, an apparatus for spending human attention well:

- capture each human judgement in reusable form (the same rubric the LLM uses), so one act of attention becomes permanent ground truth.
- measure human-vs-LLM agreement (Cohen's kappa and friends). High agreement on an axis means the LLM judge can stand in for the human there. Low agreement means it cannot.
- route to the human only what needs eyes, taste, or context: low judge confidence, high human-LLM disagreement, high stakes, and novel cases (anomalies / out-of-distribution, see clustering).

The loop: humans label the hard and the new, the LLM judge handles the rest, agreement decides where the boundary sits, and that boundary moves as the judge proves itself.

=====================

In the evaluation framework:
- humans evaluate with the same typed rubric as the LLM judge, stored in the same structure so the two are directly comparable
- human-LLM agreement is computed per rubric item; it decides when the cheap LLM judge may replace the expensive human
- human attention is triaged: escalate low-confidence, high-disagreement, high-stakes, and anomalous cases
- a human judgement, once given, is permanent ground truth and rejoins the eval corpus
