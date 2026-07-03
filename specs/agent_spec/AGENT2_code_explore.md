This agent takes the agent directory and explores it, reporting on its code structure.

This will be done summarily (because modern agents use a mix of Tree-Sitter with an LLM skill to do this, for example graphify on github).

The goal of the agent is to report on the structure of the code (to know what the agent does apart from what can be deduced from instantiating it, we can probably deduce model, prompt, hooks, but not tools and code flows and hook actions)