This agent helps the user write value-extraction functions: from a Trace (a list of message parts) to a typed value (bool / int / float / enum).

This is the operationalisation of the deterministic metric strategy (SOUL3): once you have a mapping from a trace to a typed value, scikit metrics follow.

Inputs:
- one or more example traces
- the target type (and enum values if enum)
- a natural-language description of what to extract ("the final refund amount", "was a refund tool called", "the detected intent")

Process (draft -> run -> confirm, never autonomous):
- draft a Python function extract(trace) -> bool|int|float|str
- run it against the example traces and show the outputs
- the user confirms or edits
- store it as inspectable, fingerprinted source (the Extractor object)

The stored function then runs deterministically forever. It is pure, no I/O, and does not run the agent under test.

See soul 3 and contracts/scoring_extraction_response_matrix.md.
