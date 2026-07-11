It's 2026, loops are fashionable this year.

It's difficult to define loops as separate from procedural memory (because both are 'often done generic action sequences'), but let's try anyway.

Possible loops for evaluation frameworks:
- monitor version: make a diff between two related commits in a git tree of agentic code, see how the evals changed, try to trace back the change to changes in the code or prompts, greenlight the new version or not
- get some new eval traces (say from prod, or from QA): check the result of running them through the agent, see how the agent code should be modified for bad cases, update the eval set, optionally analyse the new traces formally (X,Y|X,Y drifts, clustering of intents/X)
- red/green/blue teaming: have three different agents respectively: break the current agent code/protect the agent code from abuse/update the whole agent framework to be better
- somehow related: automated agent programming and prompt evolution, so Omar Khattab's team (GEPA/dspy/auto harness)
- somehow related: sakana.ai's Darwin Godel machine, automatic evolution of agentic code from failure cases, Alpha Evolve, Andrej Karpathy's research loop, SkillOpt. This is similar to the previous item, but more general than prompts and agents
- meta evaluation/testing of the eval: are the evals themselves covering the test domain completely and uniformly and minimally, how good are our metrics, did we handle long traces correctly
- Soheil Feizi mentions having an LLM user to drive the agents, generating not only the test cases but also reacting to the agent's completions

In the general case:
- look at existing cases, or new cases from prod, or user ideas
- try to see what's missing/broken/changed/slow, and change the eval set and the agent