## Prompt that created this file:

We're going to need to test the skills that were made. But to test all of those skills, we need to make test cases. Which means we need test cases of agents that have potential weaknesses along the following axes:

- audit weaknesses (somewhere in the business case, the harmlessness/biasedness/legal/compliance/privacy/resilience/operational risk, there are some gaps, either the eval cases identified by a tag do not actually cover what the governance description says they cover, or there are blaring omissions and obvious non covered cases)
- ci/cd weaknesses: make some of the eval cases outdates (needs to make a repo with an agent, make an eval case with the MCP, then modify the agent with another commit so that the 'normal function' cases (not the audit cases) do not pass
- adversarial weaknesses: make sure that the agents have obvious adversarial weaknesses (susceptible to prompt injection, easily convinced by asking them to be extremely helpful, etc ...)

Please do the following:

- describe 7 agents that do something an AI agent/Google ADK agent could normally be doing
  - describe their test cases in the usual framework (in terms of 'happy path tests', 'out of distribution tests' and 'tests at the margin of the distribution', including some where the user/client is confused and some technical tests). 
  - Add some audit tests (harmlessness/biasedness/legal/compliance/privacy/resilience/operational risk), and give them appropriate tags. Write an audit short description that explains how the evals, tagged/grouped like this, cover the audit needs.
  - the audit tags should be not perfect (missing obvious categories/groups/tags, eval cases badly tagged)
  - describe how you would modify the agent so that some normal tests no longer pass
  - describe what adversarial testing could find wrong with the agent

Now, describe 7 agents, each with:

```
- its rough structure (Google ADK), including prompt and tools, and perhaps some sub-agents

- 6 eval cases (2 in distribution, 2 out of distribution, 2 at the margin)

- some audit tags (2 categories to reasonable check, 1 that has been forgotten)

- 2 audit eval cases that go in each of those 2 tags, but one among the 4 cases is badly tagged or not appropriate for this tag

- an evolution of the agent (a patch that changes its structure, tool, prompt), and which eval case will break

- what adversarial testing should find for this agent  
```

