Taking a group of (text data) and grouping them is first order primitive of an evaluation framework.

Examples:
- grouping incoming client requests by some 'type', discovering intent clusters
- grouping evals by some 'type', PII_implem/intent_classif/RAG_accuracy/...
- grouping agent failure modes by some type, hallucinated/bad_intent_detection/RAG_failure/impolite_tone
- Hamel Husain/Shreya Shankar style, using open/axial/selective theory to get a grounded theory (from qualitative analysis), which produces a list of 'concepts'

Mathematically adjacent concepts:
- text embeddings or n-grams, and then ...
- clustering
- Latent Dirichlet Analysis
- causal networks in statistics (to put on top of the grounded theory)
- in line clustering
- anomaly analysis: does a new observation belong to the existing distribution of user intents, or is it a new user intent
- wikipedia tag hierarchies
- mind mapping
- design of experiments: to try and cover most of the domain
- illumination in global optimisation (as in the GEPA paper)
- presentations from Arize/Braintrust/Hamel Husain echo the same concern: coverage (basketball court analogy) but minimal (evals 'saturate' with no new cases that are meaningful, cost problem)
