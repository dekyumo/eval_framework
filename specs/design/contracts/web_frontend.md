# Contract: Web frontend (SPA)

`frontend/` (React + TypeScript, Vite) built into `web/static/`, served by Flask.

This document is the absolute blueprint for the frontend source code. It replaces the previous underspecified iterations. You must read this carefully and map it exactly to the `.tsx` files in `frontend/src/pages/` and `frontend/src/components/`.


## How to use the mockups (read this before coding the UI)

There are ten reference screens in `specs/design/mockups/NN_*/`, each with a `screen.png` (the render) and a `code.html` (Stitch's static export). Use them like this:

- **`screen.png` is the target look.** **`code.html` is a *structural hint*, not source.** Stitch emits one monolithic HTML file per screen with inlined Tailwind and **hardcoded placeholder data**. Read it to see layout, spacing, and class choices — then **rebuild as typed React components wired to the API**. Do **not** paste it in, do **not** keep its fake data, do **not** let each page carry its own copy of the shell, do **not** infer functionality only styling.
- Every screen redraws the left rail / jobs tray / context switcher. That is a Stitch artifact of per-screen generation — in code the **shell exists once** (see Component map) and the mockups are only the *content pane*.
- A mockup shows **one static instance** of each state (one frozen rubric, one crash trace, one FAIL chip). The real components are **driven by the backend data**. If you build only what the PNG shows, you've built 1 of N states.



## Application Launch and Architecture

```text
React SPA (client-side routing)  ──fetch JSON──▶  Flask /api/*  ──▶  SERVICE LAYER  ──▶  core + storage
```

- **One app, client-side routing.** Not a set of independent pages. A persistent left rail (repo/agent context + nav) and a routed content pane.
- **The API is thin.** Every `/api/*` route is a direct call into a service-layer function (the same functions the chat operator wraps). Routes do no computation, no scoring, no business logic. If a route needs logic that doesn't exist as a service function, add the service function — do not put it in the route.
- **Typed end to end.** Generate/maintain TypeScript types from the Pydantic domain models (e.g. export JSON Schema → `frontend/src/types/`). The UI never invents field names.
- **No raw JSON as a primary view.** JSON is available behind a "view raw" affordance only. Every domain object has a rendered view.
- **Git Repo Context**: The application is launched from the command line against a specific Git repository. The UI does **not** switch Git repositories dynamically.
- **Agent Path Format**: Defining an agent uses the format `python_file_path:variable_name` (e.g., `src/agents/main.py:my_agent`). The UI must explicitly display and explain this format to the user.
- **Routing**: One React SPA (React Router). A persistent left rail (Navigation menu) and a routed content pane.
- **The API is thin and ID-based.** Routes reference IDs (`case_id`, `run_id`, `dataset_id`) and fetch entities. No massive JSON passing between client and server.
- **Forms and Input**: **NEVER** use `.trim()` on every keystroke. Use debounced updates (e.g. wait 1s after typing stops) or explicit "Save" buttons so the user's cursor is not interrupted.

## Recommended Reusable Components

The previous implementation introduced several astute component concepts that should be preserved and refactored into a proper `frontend/src/components/` directory. They elegantly encapsulate domain logic into UI primitives:

- **`ResultView`**: A component that switches its rendering based on `Result.type`. It smartly renders booleans as high-visibility green `PASS` or red `FAIL` pills, while rendering enums or floats as standard badges. 
- **`BlameTag`**: A visual categorization badge for errors (`caller`, `agent`, `framework`). By mapping these to specific semantic colors, it gives users instant context on whose fault a stack trace is.
- **`MessageBubble` & `TraceView`**: A structural component that separates message parts by role (`user`, `assistant`, `tool_call`, `tool_response`) into distinct visual bubbles (e.g., tool calls styled as code blocks, assistant text as standard chat bubbles). Because it is used in Run Generation, Run Evals, and Human Feedback, it must be highly robust and upgraded to fully support Markdown rendering.
- **`ConversationBuilder` (Replacing `CaseEditor`)**: While the previous implementation used crude string parsing (newline splitting and `indexOf(':')`), the *concept* of a dedicated widget to build multi-turn conversations is essential. This must be rebuilt as a true array-based editor where users can add/remove turns, select roles from a dropdown, and input multi-line text without it breaking.
- **`ResponseHeatmap`**: A color-graded matrix table used in Campaigns. It computes an RGB scale based on cell float values, making large model-vs-case performance matrices instantly readable.
- **`ConfirmCard`**: A standardized card specifically designed to render `ActionProposal`s. It consistently presents a summary string alongside "Confirm" and "Cancel" buttons, used across both the chat operator and sensitive UI writes.
- **`LineageGraph`**: A visualizer that maps out the `AgentManifest`, differentiating the root agent from its sub-agents with distinct interactive nodes.
- **`SplitBadge`**: A simple tag to differentiate `train` (teal) and `test` (violet) splits, making dataset partitioning immediately obvious across lists and tables.
- **`RunTraceViewer`**: A wrapper component that provides the surrounding layout for selecting a run from a list, displaying its status, and placing the trace/exception/results in context. Because this layout is identical across Run Generation, Run Evals, and Human Eval, encapsulating the left-sidebar-list + right-content-pane layout is highly recommended.

## Page Blueprint: Purpose and Allowed Actions

This section explicitly defines the purpose of each page and the exact list of actions and interactions a user can perform.

### 1. Onboarding (Scan / Add Target)
**Purpose:** Define which agent in the repository will be tested and trigger the initial code scan to generate an Agent Snapshot.
**User Interactions:**
- **View Active Repo:** The user sees the absolute path to the Git repository (read-only).
- **Select/Input Agent Target:** The user selects an agent from a dropdown of detected agents, or types an agent path (`python_file_path:variable_name`).
- **Specify Commit:** The user types a commit hash or branch name (defaults to `HEAD`).
- **Trigger Scan:** The user clicks a "Scan" button. 
  - On success, the user is navigated to the Agent Graph page. 
  - On failure, the user sees a color-coded error badge (`caller` error, `agent` error, or `framework` error) along with the full traceback.

### 2. Agents (Agent Graph and Lineage)
**Purpose:** Audit what the Agent is made of (tools, sub-agents, prompts) at a specific snapshot, and view the history of snapshots.
**User Interactions:**
- **Select Snapshot:** The user selects a historical snapshot from a dropdown.
- **View Component Graph (Manifest):** The user sees a visual node graph (e.g. using React Flow) showing the root agent connected to its sub-agents and tools.
- **View Node Details:** When the user clicks a node in the graph, a side panel displays the model ID, the full prompt text, and the tools (with their type signatures) available to that node.
- **Edit Domain:** The user can edit the Agent Domain definition by typing into text areas for `description`, `in_distribution`, `distribution_margin`, and `out_of_distribution`. The user must click a "Save Distribution" button to persist these changes.
- **Initiate Comparison:** The user selects two snapshots from dropdowns and clicks "Compare" to navigate to the comparison page.

### 3. Cases & Eval Builder
**Purpose:** Create and manage individual evaluation cases (conversations) and organize them into datasets.
**User Interactions:**
- **Filter/Search Cases:** The user filters the list of cases by typing a tag, or selecting a dataset, problem type, or domain position from dropdowns.
- **Create Case via Matrix:** The user sees a matrix of Domain Position (in-distribution/distribution-margin/out-of-distribution) vs Problem Type (happy-path/technical/adversarial/client). Clicking a cell creates a new case with those properties pre-filled.
- **Name Case:** The user types a unique name for the case.
- **Assign Dataset:** The user selects a dataset from a dropdown to add the case to it.
- **Build Conversation:** The user constructs a multi-turn conversation. For each turn, the user selects the role (User, Assistant, Tool) from a dropdown, and types the message content into a multi-line text area. The user can click "Add Turn" to append a new message, or click a "Remove" button next to a turn to delete it.
- **Fault Injection:** faults can be injected into the case with the fault injector
- **Assign Split:** The user selects `train` (displayed with a teal badge) or `test` (displayed with a visually prominent violet badge) from a dropdown.
- **Attach Metrics:** The user selects existing Extractors (and types the expected ground truth) or Rubrics to be evaluated against this case.
- **Save Case:** The user clicks "Save" to persist the case.

### 4. Run Generation (Trace Generation)
**Purpose:** Execute the Agent against a Dataset to generate Traces (the raw interactions), independent of scoring.
**User Interactions:**
- **Select Inputs:** The user selects a Snapshot and a Dataset from dropdowns.
- **Run Generation:** The user clicks "Generate Traces". The UI displays a progress indicator in a jobs tray so the user is not blocked.
- **View Trace List:** The user sees a list of generated runs, named using the format `CaseName-SnapshotHash-Timestamp`.
- **View Trace Details:** When the user clicks a generation, they see the execution trace.
  - User and Assistant messages are rendered as Markdown.
  - Tool calls are rendered as distinct blocks showing the tool name and formatted JSON arguments.
  - Tool responses are rendered as distinct blocks showing the tool name and formatted JSON output.
  - If the agent crashed, the exception stack trace is displayed at the bottom of the trace with a red background.
  - Token counts and latency are displayed at the bottom.
- **Rerun Generation:** The user clicks "Rerun" on a specific trace or "Run Missing" to generate traces for cases that don't have one yet.

### 5. Run Evals (Trace Scoring & Summary)
**Purpose:** Score previously generated traces using Extractors and Rubrics.
**User Interactions:**
- **Select Inputs:** The user selects a Snapshot and a Dataset from dropdowns.
- **Trigger Scoring:** The user clicks "Run Evaluations" if there are evaluations for this snapshot and dataset that have not been run.
- **View Score Summary:** The user sees an aggregate summary at the top of the page: R2/MAPE for float metrics, F1 for booleans/enums, and average scores for rubrics.
- **View Individual Scores:** The user clicks a scored trace to see its results. 
  - For booleans, the user sees a green PASS or red FAIL badge. 
  - For other types, the user sees the extracted value.
  - If ground truth exists, it is displayed alongside the extracted value.
  - For Rubrics, the user can read the text `rationale` generated by the LLM judge.
- **Run Again:** The user clicks "Score Again" to rerun the evaluation for a specific trace.
- **Display:** if the scoring has been run, it is possible to flatten the rubrics (rubric_a.score1 to rubric_a_score_1) and use the various folding functions (% true, average, R2, MAPE, F1 score) to display a score for the snapshot and dataset

### 6. Compare
**Purpose:** Compare two Agent Snapshots to detect regressions and understand structural changes.
**User Interactions:**
- **Select Snapshots:** The user selects Snapshot A and Snapshot B from dropdowns.
- **View Semantic Diff:** The user reads a list of prompts and tools that were added, removed, or changed between the two snapshots.
- **View Regressions:** The user sees a list of metrics that degraded in performance between Snapshot A and Snapshot B.

### 7. Campaigns (Item Response Theory)
**Purpose:** Evaluate a single dataset across multiple different Judge Models to determine item difficulty and model ability.
**User Interactions:**
- **Launch Campaign:** The user chooses a name for the campaign, selects a Snapshot, an EvalDataset, types a comma-separated list of models, and clicks "Launch".
- **Separator between running and analysing a campaign**
- **Select finished campaign**: The user selects a generated and scored campaign
- **Select Metric to Analyze:** The user selects a specific Extractor field or Rubric item from a dropdown.
- **View Response Matrix:** The user sees a heatmap grid of models (rows) vs cases (columns). Cell colors correspond to the metric score (e.g., green for pass, red for fail, gradient for floats).
- **View IRT (for boolean)/Regression (for float):** The user sees the calculated "Item Difficulty" for each case and "Model Ability" for each model based on the selected metric.

### 8. Registries
The registries manage reusable evaluation criteria and metadata. These must be split into separate pages or distinct, fully-featured tabs.

#### 8.1 Datasets
**Purpose:** Manage named groups of Eval Cases.
**User Interactions:**
- **Create Dataset:** The user clicks "New Dataset", types a unique name, and clicks "Save".
- **Rename Dataset:** The user edits the name of an existing dataset and clicks "Save".
- **Delete Dataset:** The user clicks "Delete" to remove a dataset. This button is disabled if any EvalCase is currently assigned to the dataset.

#### 8.2 Tags
**Purpose:** Manage tags for filtering cases.
**User Interactions:**
- **Create/Edit Tag:** The user types a unique name, selects a color, and clicks "Save".
- **Delete Tag:** The user clicks "Delete" to remove a tag. This button is disabled if the tag is assigned to any cases (usage count > 0).

#### 8.3 Rubrics
**Purpose:** Create LLM-as-a-judge grading criteria.
**User Interactions:**
- **Create/Edit Rubric:** The user types a unique name and the main instructions ("You are a critic...").
- **Manage Fields:** The user can add multiple fields. For each field, the user types a name, selects a return type (Float, Boolean, Enum, Integer) from a dropdown, and types the field-specific LLM prompt. For Enums, the user types the allowed values.
- **View Frozen State:** If a rubric has already been used to score a run, all text inputs and dropdowns are disabled (read-only) to preserve audit history. 
- **Create New Version:** If a rubric is frozen, the user clicks "Create New Version" to duplicate the rubric into a new, editable instance.

#### 8.4 Extractors
**Purpose:** Write Python functions to extract structured data from a Trace.
**User Interactions:**
- **Create/Edit Extractor:** The user types a name, selects a return type (String, Float, Boolean, Enum), and writes Python code in a dedicated code editor block.
- **Dry-run (Test):** The user clicks "Run on sample trace" to execute their Python code against a sample trace and see the output before saving.
- **Save/Version:** When the user clicks "Save" on an extractor that has already been used, it automatically creates a new version to preserve audit history.
- **AGENT4**: the extractor author agent can be used to draft extraction functions

### 9. Human Eval
**Purpose:** Allow humans to grade traces to establish ground truth or audit the LLM judge.
**User Interactions:**
- **Search Generation:** The user selects a RunGeneration from a dropdown by its display name.
- **Read Trace:** The user views the formatted execution trace (same format as Run Generation).
- **Input Scores:** The user sees a Rubric and manually inputs their scores for each field.
- **View Agreement:** The user sees a confusion matrix and Cohen's kappa score comparing their manual human scores to the LLM judge's scores.

### 10. Chat Operator
**Purpose:** A conversational interface to the evaluation framework.
**User Interactions:**
- **Send Message:** The user types a message and hits enter to chat with the AGENT1 operator. The chat displays user messages, assistant messages, and tool outputs.
- **Confirm Actions:** When the assistant proposes a destructive or expensive action (e.g., launching a scan or a campaign), the UI displays a confirmation card summarizing the action. The user must explicitly click "Confirm" to execute it or "Cancel" to abort.

## API Routes

All routes deal with IDs and rely entirely on the service layer for business logic. They closely map to the endpoints exposed in `web/routes/__init__.py`:

### Config & Environment
- `GET /api/health`
- `GET /api/config/judge-models` (Provides default judge model and allowed panel)
- `GET /api/jobs` (Polling endpoint for async tasks)
- `GET /api/repo` (Returns Git repo info from the CLI launch path)
- `GET /api/repo/agents` (Enumerates discoverable agents)

### Snapshots & Scanner
- `POST /api/scan` (Takes `agent_path`, `commit`, triggers generation of a new Agent Snapshot)
- `GET /api/snapshots`
- `GET /api/snapshots/<id>`
- `PATCH /api/snapshots/<id>/domain` (Updates the `AgentDomain`)

### Cases
- `GET | POST /api/cases`
- `GET /api/cases/<id>`
- `POST /api/cases/<id>/copy` (Duplicates a case for easy editing)

### Runs (Generation & Evaluation)
- `GET /api/runs?snapshot_id=...` (List runs)
- `GET /api/runs/status?snapshot_id=&dataset_id=` (Checks how many traces/evals are missing for a dataset)
- `POST /api/runs/generate` (Executes the agent against a dataset to generate traces)
- `POST /api/runs/evaluate` (Scores generated traces against the dataset's metrics)
- `GET /api/runs/<id>` (Fetch a specific run trace)
- `POST /api/runs/<id>/rerun` (Regenerates the trace for a specific run)
- `POST /api/runs/<id>/rescore` (Re-evaluates the trace for a specific run)
- `GET /api/runs/<id>/scored` (Fetches the scoring results and rationales for a run)

### Registries
- `GET | POST /api/tags`, `DELETE /api/tags/<name>`
- `GET | POST /api/datasets`, `PATCH | DELETE /api/datasets/<id>`
- `GET | POST /api/rubrics`, `GET | DELETE /api/rubrics/<id>`, `POST /api/rubrics/<id>/new-version`
- `GET | POST /api/extractors`

### Campaigns & Compare
- `GET /api/compare?a=&b=` (Compares two snapshot IDs for diffs and regressions)
- `GET | POST /api/campaigns`
- `GET /api/campaigns/<id>/matrix` (Fetches the heatmap matrix for a campaign)

### Human Evaluation
- `GET | POST /api/human-eval`
- `GET /api/agreement/<rubric_id>` (Calculates Cohen's kappa and confusion matrix)

## Tests Requirements
- **Web UI Tests (Playwright)**: The entire flow must be covered by E2E testing to ensure user interactions work (e.g., building a typed rubric with fields, creating uniquely named datasets, dry-running extractors).
- **API Contract Tests**: No logic in routes; all routes parse parameters into IDs and call the service layer.