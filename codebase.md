# Project

eval_framework is software in python to evaluate AI agents written in the Google ADK framework.
It is composed of a spec, a backend written in python with flask and a Kuzu database, and a React/Vite statically compiled frontend.

# File tree
Project root
|   .env : env file with the LLM keys for the ADK (git ignored)
|   .env.example : example env file
|   .gitignore 
|   AGENTS.md : instructions for coding agents working on this repo
|   codebase.md : this file
|   pyproject.toml 
|   README.md : project overview and setup
|   run_app.py : the main entry point for the app (web, headless, or MCP mode)
|   TODO.txt
+---example_ragas_integration : examples integrating RAGAS metrics with ADK agents
|   |   README.md
|   +---scenario1_autotranslate : try to translate metrics from the ragas package to Google ADK metrics with a skill
|   |   +---example_output
|   |   \---SKILL_file
|   |       \---skills
|   |           \---ragas-metric-to-adk
|   |                   SKILL.md
|   \---scenario2_compat_layer : try to  translate genai messages to the ragas message format, and implement a RagasBaseLLM using the ADK
|       |   run_context_recall_eval.py
|       +---adk_ragas_compat
|       |       adk_agent_runner.py
|       |       adk_ragas_llm.py
|       |       adk_to_ragas.py
|       |       __init__.py
|       \---articles_rag_tool
|               articles_data.py
|               articles_retrieval.py
|               eval_state.py
|               keyword_articles_retriever.py
|               __init__.py
+---skills : Cursor agent skills for meta-loops and audits
|   +---eval_data_analysis : how to analyse the csv/markdown output
|   |       SKILL.md
|   +---eval_framework_mcp : MCP happy path and ID conventions
|   |       SKILL.md
|   +---loops_blueprint : loops (SOUL8) implemented as the host MCP injecting an agent into the eval_framework with a blueprint
|   |   |   README.md
|   |   +---adversarial : red blue green adversarial evals (as agent)
|   |   |       SKILL.md
|   |   +---audit : check NIST AI RMF declaration (as agent)
|   |   |       SKILL.md
|   |   +---ci_cd : run CI/CD regression testing (as agent)
|   |   |       SKILL.md
|   |   \---harness_optimisation : auto improve the agents from failing evals (as agent)
|   |           SKILL.md
|   \---loops_mcp : loops (SOUL8) implemented as the MCP host directly calling the eval framework using the MCP (with SKILLs.md for API guidance)
|       |   README.md
|       +---adversarial red blue green adversarial evals (as MCP)
|       |       SKILL.md
|       +---audit : check NIST AI RMF declaration (as MCP)
|       |       SKILL.md
|       +---ci_cd : run CI/CD regression testing (as MCP)
|       |       SKILL.md
|       \---harness_optimisation : auto improve agents from failing evals (as MCP)
|               SKILL.md
+---specs : root dir for all the specs written before generating the app
|   |   functional_spec.md
|   |   functional_spec_addendum.md
|   |   python_objects.md
|   +---agent_spec : the ADK agents that will provide services inside the app
|   |   |   AGENT1_chat_agent.md : legacy chat-operator agent spec
|   |   |   AGENT2_code_explore.md : an agent that looks at ADK agent code and guesses their purpose
|   |   |   AGENT3_code_mocker_and_failure_injector.md : makes mocked tools that can fail on cue
|   |   |   AGENT4_extractor_author.md : makes functions from traces to bool/int/float, to help validate traces
|   |   |   AGENT5_eval_case_writer.md : writes eval cases
|   |   |   coding_agent_structure.md : an exploration of known coding agents
|   |   \---loops
|   |           adversarial.md
|   |           audit.md
|   |           ci_cd.md
|   |           harness_optimisation.md
|   +---design
|   |   |   DESIGN.md : a stitch generated design file
|   |   |   IMPLEMENTATION.md : ENTRY POINT FOR THE SPEC, point a coding agent here to reimplement the app from scratch
|   |   |   object_model.md 
|   |   +---contracts
|   |   |       agent_scanner.md : description of the ADK object exploration and ast reading that help agent2 understand the agent
|   |   |       fault_injector.md : spec for fault injection/agent3
|   |   |       governance_nist.md : NIST AI RMF profile fields on agent snapshots
|   |   |       loops_mcp_blueprints.md : MCP tools and blueprint presets for meta-loops
|   |   |       scoring_extraction_response_matrix.md : spec for IRT/SOUL9
|   |   |       web_frontend.md : spec for the web frontend
|   |   |       worktree_runner.md : spec for git worktree isolation
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
+---src
|   \---eval_workbench
|       |   config.py
|       |   otel_config.py : OpenTelemetry trace export configuration
|       |   repo_layout.py : paths for repo root, worktrees, and data dirs
|       +---agents : the agents described in the spec
|       |   |   __init__.py
|       |   +---case_writer : writes eval cases
|       |   |   |   agent.py
|       |   |   |   case_writer_runner.py : subprocess runner for case-writer agent
|       |   +---code_explorer : analyses ADK agents
|       |   |   |   agent.py
|       |   +---extractor_author : writes functions from traces to bool/int/str
|       |   |   |   agent.py
|       |   +---fault_mocker : makes faulty tools
|       |   |   |   agent.py
|       +---analysis
|       |   |   agreement.py : computes Kappa/correlation/confusion matrix between human evals and automated evals
|       |   |   comparison.py : a diff (almost a text diff) between two agent snapshots
|       |   |   drift.py : from eval score change, decide whether an agent is OK/KO (TODO)
|       |   |   metrics.py : folding functions on metrics, num cases, num passed, etc... (TODO: use more advanced functions for sklearn.metrics)
|       |   |   response_matrix.py : the response matrix for IRT
|       |   |   validity.py : checks that scores are not going down on the 'test' set
|       +---domain : the pydantic domain objects, very similar to their spec
|       |   |   blueprint.py : blueprint presets and run results for meta-loops
|       |   |   campaign.py 
|       |   |   case.py
|       |   |   extractor.py
|       |   |   fault.py
|       |   |   governance.py : NIST AI RMF profile on a snapshot
|       |   |   gym.py : a POMDP environment (class_path) for agentic-user simulations
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
|       |   |   fault_mocker_runner.py : subprocess runner for fault-mocker agent
|       |   |   injector.py : 
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
|       |   |   |   |   CaseStatusBadge.tsx : not-gen / not-eval / ran badges on Runs and Evals
|       |   |   |   |   ConfirmCard.tsx
|       |   |   |   |   Layout.tsx
|       |   |   |   |   LineageGraph.tsx
|       |   |   |   |   MessageBubble.tsx
|       |   |   |   |   ResultView.tsx
|       |   |   |   |   SnapshotSelect.tsx
|       |   |   |   |   SplitBadge.tsx
|       |   |   |   |   TraceView.tsx
|       |   |   |   +---cases : sub components for the case builder page
|       |   |   |   |       CaseAgenticUserPane.tsx
|       |   |   |   |       CaseAgentInputPane.tsx
|       |   |   |   |       CaseConversationBuilder.tsx
|       |   |   |   |       CaseDirectInput.tsx
|       |   |   |   |       CaseGenerationPane.tsx
|       |   |   |   |       CaseListPane.tsx
|       |   |   |   |       CaseMetadataFields.tsx
|       |   |   |   |       CaseMetricsSection.tsx
|       |   |   |   |       CaseOthersPane.tsx
|       |   |   |   |       CaseSessionStateInput.tsx
|       |   |   |   |       CaseToolFaultSection.tsx
|       |   |   |   |       types.ts
|       |   |   |   +---registries : sub components for the registry page
|       |   |   |   |       DatasetRegistry.tsx
|       |   |   |   |       ExtractorRegistry.tsx
|       |   |   |   |       GymRegistry.tsx : register gyms (class_path) for agentic-user cases
|       |   |   |   |       RubricRegistry.tsx
|       |   |   |   |       TagRegistry.tsx
|       |   |   |   \---ui : shadcn components
|       |   |   |           AgentPromptInput.tsx
|       |   |   |           Button.tsx
|       |   |   |           PageLayout.tsx
|       |   |   |           Select.tsx
|       |   |   |           Textarea.tsx
|       |   |   |           Typography.tsx
|       |   |   +---pages : the main user pages
|       |   |   |       Agents.tsx : look at the agent scan results and NIST AI RMF profile
|       |   |   |       Campaigns.tsx : launches campaigns (IRT)
|       |   |   |       Cases.tsx : adds test cases
|       |   |   |       Compare.tsx : compare an agent between two scans
|       |   |   |       Evals.tsx : run the metrics on the generated Cases
|       |   |   |       HumanEval.tsx : give a human eval on a rubric
|       |   |   |       Onboarding.tsx : scans an ADK agent in a folder with AGENT2+instantiate_and_explore_agent_object_graph+ast exploration for tools/callbacks
|       |   |   |       Registries.tsx : input static data (dataset names, tag names, extraction function, Rubrics)
|       |   |   |       Runs.tsx : generates traces on Cases by running their ADK agent
|       |   |   +---types
|       |   |   \---utils
|       |   |           cn.ts
|       |   |           snapshotLabel.ts
|       |   \---tests
|       |           e2e.spec.ts : the main frontend test suite
|       |           eiffel_tap.png : image to test multimodal conversations
|       +---mcp : Model Context Protocol server exposing workbench tools
|       |   |   registry.py
|       |   |   server.py
|       |   |   __init__.py
|       |   |   __main__.py
|       +---runner : runs agents on eval cases
|       |   |   agent_runner.py : run agents on a git commit
|       |   |   agentic_sim.py : two-agent (user+solver) gym simulation loop for agentic-user cases
|       |   |   case_input.py : build ADK input payloads from case definitions
|       |   |   exec_script.py : script executed in another process for one run
|       |   |   message_parts.py : parse and normalise ADK message parts
|       |   |   trace_events.py : collect trace events from agent runs
|       |   |   worktree.py : git worktree isolation
|       +---scanner : scans an agent dir
|       |   |   agent_structure_dump.py : get hints about the agent from instantiating it and walking the object graph
|       |   |   ast_enrichment.py : get hints about the tools and callbacks by getting their source code
|       |   |   code_explorer_runner.py : run agent2 to guess expected purpose/inputs for the agent
|       |   |   errors.py : some Exceptions, many are unused
|       |   |   introspect_script.py : short script for exec in a child process
|       |   |   scanner.py : main/route
|       +---services
|       |   |   agents.py
|       |   |   benchmark.py : headless benchmark orchestration
|       |   |   blueprints.py : blueprint preset execution
|       |   |   campaigns.py
|       |   |   cases.py
|       |   |   comparison.py
|       |   |   errors.py
|       |   |   governance.py : read/write NIST AI RMF profile on snapshots
|       |   |   human_eval.py
|       |   |   registries.py
|       |   |   repo.py
|       |   |   rubric_judge_runner.py : subprocess runner for rubric LLM judge
|       |   |   runs.py
|       |   |   scoring.py : evaluate a generated trace with rubrics or extraction function + ground truth
|       |   |   snapshot_label.py
|       |   |   _conn.py
|       |   |   _ids.py
|       |   |   __init__.py
|       +---storage
|       |   |   kuzu_store.py
|       |   |   repositories.py
|       |   |   schema.py
|       +---web
|       |   |   app.py
|       |   +---routes : thin routes
|       |   |   |   agents.py
|       |   |   |   blueprints.py
|       |   |   |   campaigns.py
|       |   |   |   cases.py
|       |   |   |   governance.py
|       |   |   |   otel.py
|       |   |   |   registries.py
|       |   |   |   runs.py
|       |   +---static
|       |   |   |   index.html : the HTML for the SPA, uses the assets files compiled by Vite
|       |   |   \---assets
|       |   |           index-5464446a.css
|       |   |           index-da704a5a.js
+---tests : unit tests for the backend
|   |   conftest.py
|   |   test_agentic_sim.py
|   |   test_agent_runner.py
|   |   test_ast_enrichment.py
|   |   test_benchmark.py
|   |   test_blueprints.py
|   |   test_cases_state.py
|   |   test_case_generation.py
|   |   test_code_explorer_runner.py
|   |   test_comparison.py
|   |   test_faults.py
|   |   test_governance.py
|   |   test_input_payload.py
|   |   test_mcp.py
|   |   test_message_parts.py
|   |   test_otel_dump.py
|   |   test_registries.py
|   |   test_rubric_judge.py
|   |   test_runs_service.py
|   |   test_scanner.py
|   |   test_scoring.py
|   |   test_snapshot_label.py
|   |   test_storage.py
|   |   test_trace_events.py
|   |   test_web.py
|   |   test_worktree.py
|   +---fixtures
|   |   +---agents
|   |   |   +---clean
|   |   |   |       agent.py
|   |   |   \---malformed
|   |   |           agent.py
|   |   \---gyms
|   |       |   simple_gym.py