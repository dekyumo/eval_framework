# Contract: AgentScanner and Code Explorer (AGENT2)

`scanner/scanner.py` and `agents/code_explorer/`. The scanner pipeline turns a clean Git commit of an agent-under-test into an `AgentManifest` and an `AgentDomain`. 

This process is strictly divided into two phases:
1. **Deterministic Scan (`scanner.py`)**: A fragile but highly constrained, LLM-free extraction of the agent's structural manifest (prompts, tools, sub-agents).
2. **Semantic Exploration (AGENT2 / `code_explorer`)**: An LLM-assisted draft of the agent's operational domain boundaries (what it can and cannot do).

## 1. Deterministic Scanner (`scanner.py`)

### Responsibility
Given an **`AgentTarget` (repo + `agent_path`)** and a clean commit, produce a deterministic `AgentManifest` for **that specific agent** (agents, tools, models, prompts, edges) by combining **instantiation** (what ADK exposes when the agent object is built) with **AST inspection** (what only the source reveals: tool bodies, hooks, code flow). 

It does **not** run the agent. It strictly instantiates and reads structure.

### Mechanism & Isolation
Instantiation happens inside a Worktree subprocess (see `worktree_runner.md`), so scanning a faulty or malicious commit never crashes or pollutes the main framework process.

1. **Preconditions**: Check if repo exists, commit exists, and the tree is clean.
2. **Resolve Path**: Find the target (e.g. `pkg.mod:root_agent`).
3. **Instantiate (Subprocess)**: The Worktree runner executes a tiny introspection script that imports the agent and outputs a JSON dump of the ADK object graph (models, raw prompt templates, sub-agent edges).
4. **AST Scan (Main Process)**: Uses Python's `ast` module to read the agent's source code files. It extracts exact tool function signatures and raw source code segments.
5. **Reconciliation**: Merges the ADK object graph with the AST scan to create the `AgentManifest`. Prompts and Tools are hashed/fingerprinted based on their normalized raw text.

### Error Taxonomy (The Blame Fence)
When the scanner fails, it is critical to attribute blame correctly. All exceptions inherit from `ScannerError`.

| Exception | Category | Meaning / who is to blame |
| --- | --- | --- |
| `RepoNotFoundError`, `CommitNotFoundError`, `DirtyRepositoryError` | **CallerError** | The framework was called wrong (bad path / dirty tree). |
| `AgentEntrypointNotFound`, `UnsupportedAgentStructure`, `AgentImportError` | **AgentError** | The agent-under-test is malformed/unsupported. Carries the agent's underlying traceback. |
| `ScannerInternalError` | **FrameworkError** | A bug in the scanner. Wraps any unexpected exception with full context. |

## 2. Semantic Code Explorer (AGENT2)

### Responsibility
After the deterministic `AgentManifest` is built, the framework needs to establish an `AgentDomain`. The domain defines the operational boundaries of the agent (used later to categorize evaluation cases).

Because understanding the boundaries of an agent requires reading and comprehending its instructions and tool capabilities, this is delegated to **AGENT2 (`code_explorer`)**.

### Mechanism
AGENT2 acts as a domain expert and Product Manager.
1. **Input**: It is fed the deterministic structure extracted by the scanner (the ADK agent definition, instructions, and the source code for its tools).
2. **Process**: The LLM analyzes the prompts and tool capabilities.
3. **Output**: It generates a structured `AgentDomain` object consisting of:
    - `description`: A high-level explanation of the agent's functionality.
    - `in_domain`: A list of tasks the agent is explicitly designed to handle.
    - `out_of_domain`: A list of tasks the agent is fundamentally incapable of, or explicitly restricted from handling.
    - `domain_margin`: Tasks that represent edge cases or exist in a gray area of the agent's capabilities.

### Integration
The `AgentDomain` produced by AGENT2 is saved to the `AgentSnapshot`. It is treated as a **draft**. A human operator views this draft in the UI (on the `Agents.tsx` page) and can edit or refine the boundaries before saving the final domain definition. 

By separating the deterministic structural scan from the LLM-assisted domain draft, the framework ensures the core `AgentManifest` remains byte-identical and perfectly reproducible for any given commit, while still automating the tedious documentation of the agent's operational boundaries.