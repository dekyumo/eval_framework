A rubric is how you turn a quality you cannot verify into a number you can.

Honesty first: there is no single grand theory of rubric writing. It is borrowed from several places that each solved a piece of it:
- educational assessment: analytic vs holistic rubrics, scoring anchors, level descriptors
- social-science measurement: operationalisation and construct validity, turning a vague construct ("helpful") into something observable
- survey design: the hygiene of good items, no double-barrelled questions, no leading wording, mutually exclusive options
- psychometrics: reliability, the empirical test that a rubric actually works

The job of a rubric: an unverifiable trace (a tone, a helpfulness, a "is this a good refund reply") has no extractable ground truth. The rubric is the operationalisation step that decomposes that fog into axes, each of which CAN be judged, by a human or an LLM, with some consistency.

What a good rubric looks like:
- decomposed, not holistic. A holistic "rate this 1-10" is cheap and opaque. Analytic axes (was the policy stated, was the tone calm, was the order id used) are diagnostic and comparable.
- axes roughly MECE: independent of each other, together covering the construct.
- each axis objectively phrased, with anchors. "Quality: 1-10" is not a rubric, it is a vibe. "Did the reply cite the actual refund window? yes/no" is a rubric item.
- typed items: boolean, enum, number. The type is what lets human and LLM answers be compared by the right statistic later.

The empirical test (this is the teeth):
- a rubric is good if two independent raters applying it agree. Inter-rater reliability.
- when your human and your LLM judge disagree, the first suspect is the rubric, not the rater. A disputed item is usually an item that was never objective. Low agreement is a design signal: split the axis, anchor it, or delete it.

Pairwise is a rubric too, and a good trick: humans and LLMs are both better at relative judgement than absolute scoring ("which of these two is better" beats "score this 0-100"). It collapses a noisy absolute scale into a cleaner comparison.

Once traces are scored against a rubric, the rubric is frozen. Changing its axes or its prompt changes the meaning of the number, so changing a rubric is a new rubric (see MLOps).

=====================

In the evaluation framework:
- rubrics are first-class and typed (boolean / enum / number per axis)
- the SAME rubric is applied by the LLM judge (SOUL6) and the human (SOUL12); that shared language is the whole point, it is what makes their agreement measurable
- ship default rubric frameworks (quality, tone, safety) and push users to write domain-specific ones
- track inter-rater agreement per item; treat a low-agreement item as a broken rubric, not a broken rater
- a rubric is versioned and frozen once used
