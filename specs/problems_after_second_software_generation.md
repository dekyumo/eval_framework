- pointing the software at a git repo, and specifying an agent is still clunky
    - specify a path with a .git
    - enter an agent path (python_path:variable_name), but the python path might be dir\dir:root_agent or dir.dir:root_agent
    - this silently switches the git dir, and the Kuzu database path, making the agent list empty (def add_repo: set_repo_singleton())
    - -> the app should be launched with a git repo as argument, and the agent path format should be explained more
    - OR -> the app should completely specify how to handle multiple git repos at the same time
- the Registries web interface was underspecced
    - all the registries: tags, rubrics, extractors, datasets are all not working for various reasons (tags backend has a problem in its Cypher-like query and raises an exception, Rubrics add button does not give options to build a typed rubric, extractors page just show "TODO, agent v4", Datasets add just adds a Dataset with the default name which is the same name and that indefinitely)
    - this would have required a full spec, which page, which button, what happens when you click, what cannot be duplicated
    - the agent somehow decided to make all these complex interactions on one React page, and probably got hit by the context window limit
    - and, of course, this would have needed web testing (either playwright or agent browser use)
    - the spec was:
        - Tags: a name and a color, the name must be and stay unique, name and color can be edited, only tags that are not in use can be deleted
        - Rubrics: a unique name for the rubric, a list of fields (field_name and type such as float or bool or Enum, in the Enum case it can be specified with a list of unique string values), only rubrics that are not in use can be modified. A rubric also needs a prompt ("You are a critic that will evaluate the answer below on the following axes").
        - Extractors: a list of named python functions that take schema.Trace as input and returns a value (string, float, bool, enum)
        - Datasets: not sure whether this is useful. A Dataset is a group of evals. It is just a name. The name must be unique and cannot be deleted unless no EvalCase uses it.
    - -> fully specify the user interactions, and force web testing
    - -> decide whether named datasets are actually useful, or agent_name and tags are sufficient. Named datasets make it easier to run campaigns
- the agent graph view has been badly specified
    - graph view could mean one of two things, a graph of the agent and its sub-agents and tools OR a graph of the agent through the various git commits
    - this has not been specified and the implementing coding agent made a choice
    - -> fully specify this
- the interface to make a trace has been underspecified
    - the matrix (in domain/domain margin/out of domain TIMES path type is maybe not relevant, because we want mainly problematic path types in domain)
    - the dataset id was missing
    - the interface to specify the case is weird, the conversation is a textarea with (user: utterance\nassistant: utterance\nuser:utterance...), but the roles are not stronly type, it is not possible to specify utterances of more than one line, and it is not possible to add images/audio. Defining the case's conversation needs a dedicated .tsx/widget.
    - it is not possible to make add metrics to a case
        - a metric in a case is one of a:
            - a rubric (it contains a prompt, it returns structured output, its rubric)
            - an extractor + ground truth
    - the interface to view and make traces needs to have a dataset dropdown
- the interface to run a trace has been underspecced again:
    - currently lets the user run one case on one snapshot (but doesn't display the commit, only the agent name). No possibility to run on a full dataset. 
    - can change the model, which was not specified. In ADK the model is a property of the agent. Only the Campaign/Item Response Theory page should be able to change the agent
    - need to check that every case is run once on one snapshot (since LLMs are probabilistic, we could be running the same evals indefinitely with different results)
    - -> running an eval (generating traces) and scoring (launching the extractors and the LLM as judge on the rubrics) are two completely separate processes. This is not properly defined in the spec. For traces from prod, the trace is already generated and only the scoring happens.
    - -> separate the Runs tab into Run Generation (takes a snapshot and a dataset) and Run Evals (takes a generation on a run and a dataset)
- How to handle a run trace that's in error, how to delete it, how to generate it again, is underspecified
    - there is not error/exception field on a trace
    - it might need to be a first order member of a trace (the user/developer might want erroneous tool input to throw an exception)
    - this would change the trace structure a bit (from MessageParts[] to either (MessageParts[]|Optional[Exception]) or make the exception one of the message parts (if the agent is supposed to handle it)). Since MCP has tool failure semantics, it is probable that the signature could even be (MessagePartsOrException[],Optional[FinalException]) where intermediate exceptions are tool use exceptions ).
- How to show the result of a Run Eval:
    - initially, the eval results just show (PASS/FAIL for a rubric, whereas it's a list of metrics). Extractor functions do not show their inner workings, just the result, so they might actually be badly programmed.
    - extractor function being written by the user, they might throw exceptions. The result needs to be extracted_value + ground_truth_value + PASS/FAIL (this will be transformed into an R2/MAPE/F1score/... anyway)
    - the rubrics need to show every result field, an the 'rationale', the text result before the structured output, if any.
    - they need a 'Run Again' button, same as Run Generation
- Running rubrics:
    - create a pydantic type on the fly (no caching) from the rubric description, one field and one "rationale" field per rubric output field, need to sanitise the names
    - spin an ADK agent:
       - prompt = rubric prompt + "Trace to judge" + trace + "additional instructions per field" + "\n".join(field_name+":"+field_specific_prompt)
    - using the ADK lets us skip the model switching (wiring to different APIs)
- Running campaigns:
    - campaigns are run on a snapshot (so agent name + commit), with an eval dataset, and a list of models
    - the campaign and its derived IRT score suppose that the response is some kind of true/false. But the result of a RunEval is a list of (extracted_value+ground_truth_value OR multi dimensional rubric). We might need to run the campaign, and run the IRT on all booleans, and a regular regression on all float scores. The problem is that not all EvalRuns have the same rubric. The regression/IRT could be run separately on each rubric item/each extractor value.
    - just to confirm, once the campaign has been run, it is easy to ask the backend to do an IRT/regression on one of the eval fields. It is not necessary to display all the regressions/IRT at the same time. Only a dropdown on extractor_field/rubric_field is necessary.

- Human Eval:
    - Human evals need to find an RunGeneration, preferably one that has no manual rubric.
    - the cases have no names, and the RunGeneration are all hashes, the generations need a better display name (see conclusions)
    








    




CONCLUSION:

EvalCases need a name. They are very difficult to find with their hash only. A full name for a generation (EvalCaseName-ModelName-Hash) would make it even easier.

This will come as a surprise to noone. The exact shape of the web interface has to be specified, in plain English or Playwright test cases. I thought the model would have more common sense.

The interface is quite opinionated about not letting the user change anything once it's been used in a run. This is because it tries to act as both an eval interface and an audit interface. If the user makes a benign mistake (for example the creates an extractor function with a bug), and has to change everything by hand, this could be incredibly frustrating. The audit properties and eval properties of the app have to be properly merged together.

Being able to run n times per case has not been specified, nor has the ability to run m rubric evals per run.

Missing values ! Sometimes the extractor doesn't return a value. Sometimes the ground truth is None (if the user didn't specify a budget, for example). This is an ML app, and somehow missing values should be handled correctly, both in the ground truth and associated metrics.

Also, somehow unrelated. Reading the DeepEval docs. Scores are boolean once you add a threshold. This is standard logistic regression common sense, and cost aware ML optimisation of the threshold. After taking a look at the Ragas docs as well, a conclusion is that it would be easy to use those metrics in the framework, but it needs a compatibility shim. Simply put, every agent library on the planet has a reimplementation of MessagePart, Trace, LLM, Prompt, and a compatibility layer would have to be built for each one. Making the RAG metrics available is doable, detecting RAG use in ADK agents is easy: one of their tools is a VertexAiSearchTool.

The vocabulary chosen by the implementing LLM is quite bad. The training and test set (SOUL13) is called optimisation/judging instead of standard test/train or test/validation. The 'in domain/margin of domain/out of domain' is called 'in domain/margin/ood'. The specs should reflect standard nomenclature.

There is no summary page. The spec (SOUL3) says that you can take all the evals for a given dataset+snapshot, and summarise them. So total R2/MAPE for float evaluator functions, total F1 for bool evaluator function and enum evaluator functions, average score for rubrics. This is not done. This means we're not properly evaluating snapshots yet.

This could be run from the commandline for CI/CD. This has not been planned. This is fortunately easy to implement, because the repo is chosen as a commandline argument, and all the routes in the site have an implementation in src/eval_workbench/services, making it easy to run generation then evals on a new agent HEAD and output a report.

A problem with the above dev (run CI/CD from the commandline) is that services are badly defined. They do not reference IDs. The route function signature for scoring a generated run is eval(PydanticClassTrace, PydanticTraceMetrics). In other words, the full pydantic object goes through the UI, and it is sent back to the backend to score the runs. This will make Agent1(the chat helper) more difficult to implement, and the commandline more difficult to implement.

A common pattern of use is that someone receives a group of faulty traces (from QA or prod or another developer). Those traces need to be analysed in two ways: a human readable explanation for the failure AND a taxonomy of failures (SOUL2). This is currently unsupported. This is also out of scope.

MINOR ISSUES:
- every textbox has .trim(), which makes it impossible to types spaces
- some textboxes send an update to the backend with every keystroke
- Composer has a tendency to pre-validate all text fields (.trim() text, remove period on floats, etc ...) but does it on every keystroke, and prevents typing correct values
- there is no password and no audit log: this was done on purpose for simplicity, passwords could be added with the web framework (flask password, django password), audit trails would have to be specified
- the site doesn't look as good as in the mockups, the implementing agent didn't do a super duper job when extracting the tailwind and structure. Also the mockups have slight variations (for example in what the left navigation menu looks like, maybe requiring further guidance)
- display of traces could display markdown correctly
