The agent that replies to the user in the main interface has the following structure:
- a generic ADK agent that has access to tools that can access the same functionalities as the web interface

It can also handoff the conversation to three sub agents:
- an agent that receives an erroneous trace (maybe from prod, maybe from eval), a full agent snapshot (so prompts and code structure), and outputs an explanation of why it failed
- an agent that has a registry of text clustering algorithms, and will classify the reasons for failure into categories, as in the phenomenological classification
- an agent that takes two snapshots, and a trace, and tries to explain why a trace is in failure (regression explanation and classification)

This implements the two first loops in the LOOPS soul.
