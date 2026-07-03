# Contract: Chat Operator (AGENT1)

`agents/chat_operator/` (AGENT1). The chat operator is an ADK agent designed to assist the user by answering questions and executing the framework's workflow on the user's behalf. 

## Principle
The agent serves as an alternative, conversational frontend to the Evaluation Workbench. The agent does not execute raw Python code against the repository or compute scores directly. Instead, the agent is provided with **tools that map directly to the framework's service layer/API routes**.

The agent is just another client of the contract layer, alongside the React SPA.

## Complete Workflow Support
The agent's prompt explicitly outlines the complete evaluation workflow it is capable of assisting with. Its tool surface must provide coverage for all of these actions:
1. **Targeting & Scanning**: Pointing the framework at a Git repository and scanning an agent path at a specific commit to generate an Agent Snapshot.
2. **Datasets & Cases**: Creating named Datasets, creating Tags, and creating EvalCases (multi-turn conversations with split, domain position, and problem type) assigned to Datasets and Tags.
3. **Evaluation Criteria**: Creating Extractors (evaluator functions), Rubrics (for unverifiable domains), and attaching these metrics to EvalCases.
4. **Generating Traces**: Running a Dataset against an Agent Snapshot to generate execution traces.
5. **Scoring**: Running Extractors and Rubrics against the generated traces.
6. **Reporting & Campaigns**: Summarizing run results, comparing two snapshots to find regressions, and launching Campaigns to evaluate cases across multiple LLM models (IRT/Response Matrix).

## Tool Surface and Approvals (Crucial)
Wrap the framework's service functions as ADK `FunctionTool`s. 

Because the agent interacts with the exact same service layer as the React frontend, it must adhere to strict safety boundaries. Tools are split into two categories:

### 1. Read Tools (Unrestricted)
The agent can freely execute read-only tools to answer user questions, summarize data, or gather context. 
Examples (based on backend routes):
- List Snapshots, List Cases, List Datasets, List Tags, List Extractors, List Rubrics.
- Get Snapshot, Get Case, Get Run.
- Compare Snapshots, Fetch Campaign Matrix, Get Run Summary.

### 2. Write / Expensive Tools (Require UI Confirmation)
Any tool that creates, modifies, deletes data, or triggers expensive execution (like invoking the target agent or LLM judges) **must not execute immediately**. 

Instead, the tool function must intercept the call and return a structured **`ActionProposal`** back to the UI. The UI will render this proposal as a `ConfirmCard`. The action is only executed if the human clicks "Confirm" in the frontend. 

Examples of restricted tools:
- `scan_agent`
- `create_case`, `update_case`, `create_dataset`, `create_rubric`, `create_extractor`
- `run_generation` (running traces)
- `run_evaluations` (scoring traces)
- `run_campaign`
- Any `delete_*` action.

This read vs. confirm pattern keeps the human in the loop and ensures an LLM cannot autonomously wipe the database or launch a massively expensive matrix of LLM calls without explicit consent.

## Streaming
Agent turns are served over Flask SSE. The stream must differentiate between text chunks (which the UI renders as assistant messages), tool calls, and `ActionProposal`s (which the UI renders as interactive confirmation cards).

## Dogfooding
The ultimate test of the evaluation framework is its ability to evaluate itself. Once the framework is running, the user can point the scanner at `src/eval_workbench/agents/chat_operator`, create evaluation cases for the operator itself, and score the operator's traces using the platform.