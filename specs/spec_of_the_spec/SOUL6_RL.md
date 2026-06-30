Agentic traces are stronly related to the field of RL on LLMs, in particular:
- RLHF
- GRPO
- LLM as judge

========

Current practice of evaluation requires trajectory sampling and LLM as judge evals to be run 3 times, and the mean/stdev to be computed. But this is also a GRPO step.