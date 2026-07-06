# Project

eval_framework is software in python to evaluate AI agents written in the Google ADK framework.
It is composed of a spec, a backend written in python with flask and a Kuzu database, and a React/Vite statically compiled frontend.

# File tree
Project root
|   .env : env file with the LLM keys for the ADK (git ignored)
|   .env.example : example env file
|   .gitignore 
|   codebase.md : this file
|   pyproject.toml 
|   run_app.py : the main entry point for the app
|   TODO.txt
+---scripts
|       refresh_certs.py
|       
+---specs : root dir for all the specs written before generating the app
|   |   functional_spec.md
|   |   functional_spec_addendum.md
|   |   python_objects.md
|   |   
|   +---agent_spec : the ADK agents that will provide services inside the app
|   |       AGENT1_chat_agent.md : a general agent with access to all the routes as tools
|   |       AGENT2_code_explore.md : an agent that looks at ADK agent code and guesses their purpose
|   |       AGENT3_code_mocker_and_failure_injector.md : makes mocked tools that can fail on cue
|   |       AGENT4_extractor_author.md : makes functions from traces to bool/int/float, to help validate traces
|   |       AGENT5_eval_case_writer.md : writes eval cases
|   |       coding_agent_structure.md : an exploration of known coding agents
|   |       
|   +---design
|   |   |   DESIGN.md : a stitch generated design file
|   |   |   IMPLEMENTATION.md : ENTRY POINT FOR THE SPEC, point a coding agent here to reimplement the app from scratch
|   |   |   object_model.md 
|   |   |   
|   |   +---contracts
|   |   |       agent_scanner.md : description of the ADK object exploration and ast reading that help agent2 understand the agent
|   |   |       chat_operator.md : a description of the code around agent1
|   |   |       fault_injector.md : spec for fault injection/agent3
|   |   |       scoring_extraction_response_matrix.md : spec for IRT/SOUL9
|   |   |       web_frontend.md : spec for the web frontend
|   |   |       worktree_runner.md : spec for git worktree isolation
|   |   |       
|   |   \---mockups : Google Stitch generated HTML mock designs (one HTML mockup and a png in each dir)
|   |       +---01_add_target_scan_onboarding
|   |       +---02_agent_lineage
|   |       +---03_eval_case_builder
|   |       +---04_trace_viewer_scoring
|   |       +---05_compare_snapshot_diff
|   |       +---06_campaign_response_matrix
|   |       +---07_registries_rubrics_frozen
|   |       +---08_extractor_authoring
|   |       +---09_human_evaluation
|   |       \---10_chat_operator
|   |       
|   \---spec_of_the_spec : the mathematical and software development principles underlying the evaluation workbench
|           SOUL10_FAULT_INJECTION.md : we can inject faults into the tools
|           SOUL11_RUBRICS.md : we will use rubrics
|           SOUL12_HUMAN_IN_THE_LOOP.md : where human judgement is used
|           SOUL13_VALIDITY.md : we still need to have a separate train and test set for evals
|           SOUL1_TEVV.md : software must be tested and verified against spec, on the technical and domain axes
|           SOUL2_PHENOMENOLOGICAL_CLUSTERING.md : grouping traces that are similar is a first order action
|           SOUL3_METRICS.md : we'll be measuring things
|           SOUL4_MLOPS.md : we can borrow concepts from MLOps
|           SOUL5_OBSERVABILITY.md : we'll be observing traces
|           SOUL6_RL.md : we'll be generating and scoring traces, similar to RL
|           SOUL7_GOVERNANCE.md : this software helps AI governance
|           SOUL8_LOOPS.md : there can be meta agentic loops around this software
|           SOUL9_IRT.md : we can use ItemResponseTheory to judge model strength and case difficulty
|           
+---src
|   \---eval_workbench
|       |   config.py
|       +---agents : the agents described in the spec
|       |   +---case_writer : writes eval cases
|       |   |       agent.py
|       |   +---chat_operator : general helper
|       |   |   |   agent.py
|       |   |   |   tools.py
|       |   +---code_explorer : analyses ADK agents
|       |   |   |   agent.py
|       |   +---extractor_author : writes functions from traces to bool/int/str
|       |   |   |   agent.py
|       |   +---fault_mocker : makes faulty tools
|       |   |       agent.py
|       +---analysis
|       |   |   agreement.py : computes Kappa/correlation/confusion matrix between human evals and automated evals
|       |   |   comparison.py : a diff (almost a text diff) between two agent snapshots
|       |   |   drift.py : from eval score change, decide whether an agent is OK/KO (TODO)
|       |   |   metrics.py : folding functions on metrics, num cases, num passed, etc... (TODO: use more advanced functions for sklearn.metrics)
|       |   |   response_matrix.py : the response matrix for IRT
|       |   |   validity.py : checks that scores are not going down on the 'test' set
|       +---domain : the pydantic domain objects, very similar to their spec
|       |   |   campaign.py 
|       |   |   case.py
|       |   |   extractor.py
|       |   |   fault.py
|       |   |   human_eval.py
|       |   |   manifest.py
|       |   |   result.py
|       |   |   rubric.py
|       |   |   run.py
|       |   |   snapshot.py
|       |   |   tag.py
|       |   |   trace.py
|       +---extraction
|       |   |   extractor.py : run one extraction function
|       +---faults
|       |       injector.py : 
|       +---frontend
|       |   |   index.html
|       |   |   package-lock.json
|       |   |   package.json
|       |   |   playwright.config.ts
|       |   |   postcss.config.js
|       |   |   tailwind.config.js
|       |   |   vite.config.ts
|       |   +---playwright-report : e2e test output
|       |   +---src
|       |   |   |   App.tsx
|       |   |   |   index.css : unused (tailwind)
|       |   |   |   main.tsx
|       |   |   |   
|       |   |   +---components : reusable components
|       |   |   |   |   BlameTag.tsx
|       |   |   |   |   ConfirmCard.tsx
|       |   |   |   |   Layout.tsx
|       |   |   |   |   LineageGraph.tsx
|       |   |   |   |   MessageBubble.tsx
|       |   |   |   |   ResultView.tsx
|       |   |   |   |   SplitBadge.tsx
|       |   |   |   |   TraceView.tsx
|       |   |   |   |   
|       |   |   |   +---registries : sub components for the registry page
|       |   |   |   |       DatasetRegistry.tsx
|       |   |   |   |       ExtractorRegistry.tsx
|       |   |   |   |       RubricRegistry.tsx
|       |   |   |   |       TagRegistry.tsx
|       |   |   |   |       
|       |   |   |   \---ui : shadcn components
|       |   |   |           Button.tsx
|       |   |   |           PageLayout.tsx
|       |   |   |           Select.tsx
|       |   |   |           Textarea.tsx
|       |   |   |           Typography.tsx
|       |   |   |           
|       |   |   +---pages : the main user pages
|       |   |   |       Agents.tsx : look at the agent scan results
|       |   |   |       Campaigns.tsx : launches campaigns (IRT)
|       |   |   |       Cases.tsx : adds test cases
|       |   |   |       ChatOperator.tsx : general chat/AGENT1
|       |   |   |       Compare.tsx : compare an agent between two scans
|       |   |   |       Evals.tsx : run the metrics on the generated Cases
|       |   |   |       HumanEval.tsx : give a human eval on a rubric
|       |   |   |       Onboarding.tsx : scans an ADK agent in a folder with AGENT2+instantiate_and_explore_agent_object_graph+ast exploration for tools/callbacks
|       |   |   |       Registries.tsx : input static data (dataset names, tag names, extraction function, Rubrics)
|       |   |   |       Runs.tsx : generates traces on Cases by running their ADK agent
|       |   |   |       
|       |   |   +---types
|       |   |   \---utils
|       |   |           cn.ts
|       |   |           
|       |   +---test-results
|       |   |       .last-run.json
|       |   |       
|       |   \---tests
|       |           e2e.spec.ts : the main frontend test suite
|       |           
|       +---runner : runs agents on eval cases
|       |   |   agent_runner.py : run agents on a git commit
|       |   |   exec_script.py : script executed in another process for one run
|       |   |   worktree.py : git worktree isolation
|       +---scanner : scans an agent dir
|       |   |   agent_structure_dump.py : get hints about the agent from instantiating it and walking the object graph
|       |   |   ast_enrichment.py : get hints about the tools and callbacks by getting their source code
|       |   |   code_explorer_runner.py : run agent2 to guess expected purpose/inputs for the agent
|       |   |   errors.py : some Exceptions, many are unused
|       |   |   introspect_script.py : short script for exec in a child process
|       |   |   scanner.py : main/route
|       +---services
|       |   |   scoring.py : evaluate a generated trace with rubrics or extraction function + ground truth
|       +---storage
|       |   |   kuzu_store.py
|       |   |   repositories.py
|       |   |   schema.py
|       +---web
|       |   |   app.py
|       |   +---routes : thin routes
|       |   |   |   agents.py
|       |   |   |   campaigns.py
|       |   |   |   cases.py
|       |   |   |   registries.py
|       |   |   |   runs.py
|       |   +---static
|       |   |   |   index.html : the HTML for the SPA, uses the assets files compiled by Vite
|       |   |   \---assets
|       |   |           index-4376408d.js
|       |   |           index-fd1814df.css
+---tests : unit tests for the backend
|   |   conftest.py
|   |   test_agent_runner.py
|   |   test_scanner.py
|   |   test_scoring.py
|   |   test_storage.py
|   |   test_web.py
|   |   test_worktree.py
|   |   
|   +---fixtures
|   |   \---agents
|   |       +---clean
|   |       |       agent.py
|   |       |       
|   |       \---malformed
|   |               agent.py
        
