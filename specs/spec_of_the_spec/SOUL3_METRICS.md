The evaluation framework scores realisations of stochastic processes (potentially non observable, for live coding agents for example).

The two basic objects it operates on are:
- agentic traces: a list of message parts (system messages, user messages, assistant messages, text/multimedia, tool calls and responses)
- results: float (scores) or binary (pass/fail)

Typical composition of those two are:
- an agentic trace is examined for a ground truth (is the final numerical result correct, is the intent correctly detected, is there the necessary tool call, how would you rate the quality /100)
- two agentic traces are compared to see which one is better (by a human or another agent)
- two agentic traces are compared, one is a reference/golden trace

Scores can be compared (between code versions, between models underlying the agent, ...). For rubrics, the agreement between raters (between two humans, a human and an LLM as judge, two LLMs can also be computed).

Hamel Husain points out several times that binary is easier than numeric scores, because scores are somewhat arbitrary.

This is also influenced by the verifiable/unverifiable domain dichotomy. Unverifiable domains force us to use LLM-as-judge or agents as judge, and this is true in the evaluation framework as well.

Because we need LLMs as judge, and because traces are highly dimensional, rubrics are a first order concept.




============================================

In the code this is expressed by:
- messages do not exist, the trace is the unit of agentic evaluation
- given a mapping from a trace to a float/binary/enum, we can use scikit metric routines
- agentic traces are notoriously difficult to evaluate, and might require agent-as-judge

   