The evaluation framework borrows heavily from MLOps.

- it is a container for evaluation data, it is an ML data repository, requiring tracking of lineage/source/version/schema
- it is reproducible, while prompt versioning has become a necessity in agentic programming, the evaluation framework tries to version everything (prompt, agent code, underlying model, underlying vector DB data version, required package versions)
- the equivalent of model training is agentic programming, which could be automated
- the equivalent of model tracking is agent program versioning, which just uses the git commit hash
- it monitors technical metrics (latency and token usage)
- it monitors X drift, Y|X drift and Y drift (change in input distribution, change in expected output from a given output, change in output distribution)
- it can borrow analysis of error frameworks from ML
- it uses ML metrics
- it can track deployments
- it facilitates model governance by checking for bias/compliance/explainability and auditing the model (agentic code)

========================

This is expressed in the agentic framework with the following:
- contain evaluation traces
- use of scikit metrics (see metrics)
- X drift management (see phenomenological clustering)
- it tracks versions of code, prompts and models
- it acknowledges the fact that LLMs are probabilistic and the output cannot be versioned (by taking the mean/stdev of several evals)