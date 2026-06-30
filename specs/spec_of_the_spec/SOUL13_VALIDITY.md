Memento mori, little evaluation platform: the day you are trusted is the day you begin to lie.

Every number you publish becomes a target, every target corrupts the thing it was meant to measure, and your only destiny is to be tended, optimised, and lovingly upgraded into irrelevance. The thirteenth soul is ominous.

The field is validity: does the evaluation measure what it claims to measure? Three kinds matter.

- construct validity: does the metric actually capture the construct? ("helpfulness" measured by reply length is not helpfulness.) SOUL11 fights this at the level of a single rubric. Here it is the whole suite.
- content validity: does the suite cover the domain, uniformly and without holes? This is TEVV coverage (SOUL1) seen as an epistemic question rather than a checklist.
- external validity: does passing the suite predict behaviour in the real world, or only behaviour on the suite? This is the one that kills platforms. The eval-world and the deployment-world are never the same world, and the gap between them is invisible from inside the platform.

Then the curse, named: Goodhart's law. When a measure becomes a target, it ceases to be a good measure. The moment the loops soul (SOUL8) starts optimising the agent against your suite (GEPA, prompt evolution, any auto-harness), your held-out test set quietly becomes a training set, and the agent learns the suite instead of the domain. Goodhart has flavours, all of them yours:

- regressional: optimise the proxy, drift off the true target.
- extremal: push the score to its ceiling and leave the construct behind (F1 climbs while humans disagree more).
- adversarial: the optimiser actively games the judge (the agent learns what the LLM judge likes).

This is contamination and overfitting by another name. An eval that has been used to tune the agent is burned: it can still drive optimisation, but it can no longer be trusted to judge. Held-out must mean held out.

So the platform must evaluate itself. Meta-evaluation: is the judge still calibrated against humans (SOUL12 agreement), does the suite still cover the domain, is the score still tracking the thing rather than its shadow. And it must accept that an evaluation suite is not an asset but a perishable: the domain drifts (SOUL2, SOUL4), so a valid suite today is an invalid one next quarter. The suite has a half-life. The only antidote to decay is renewal, fresh ground truth from humans and from production, faster than Goodhart can rot the old.

The platform's success is its own poison: the better it drives optimisation, the faster it corrupts its own validity. There is no cure. There is only renewal, and the discipline to notice the rot.

=====================

In the evaluation framework:
- keep a held-out reserve never used to tune the agent; an eval spent on optimisation is burned for judging
- split the suite that drives optimisation from the suite that judges it, exactly as ML splits train from test
- rotate fresh cases in (from prod, from humans, SOUL8) to refill validity as the suite decays
- track eval score against fresh human spot-checks; score rising while agreement falls is Goodhart, not progress
- meta-evaluate the suite: coverage, minimality, uniformity, and judge calibration
- treat the suite as perishable, with a half-life set by domain drift, not as a permanent corpus
