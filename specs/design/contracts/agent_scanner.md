# Contract: AgentScanner (FRAGILE)

`scanner/scanner.py`. Turns a clean commit of an agent-under-test into an `AgentManifest`. This is the most ADK-version-sensitive component; it is fenced so that when it fails, blame is attributable to one of three causes, never to "oopsie".

## Responsibility

Given a repo path and a clean commit, produce a deterministic `AgentManifest` (agents, tools, models, prompts, edges) by combining **instantiation** (what ADK exposes when the agent object is built) with **AST inspection** (what only the source reveals: tool bodies, hooks, code flow).

It does **not** run the agent. It instantiates and reads structure.

## Interface

```python
def scan(repo_path: Path, commit: str) -> AgentManifest: ...
```

Identity: the clean commit *is* the agent. `scan` is a pure function of `(repo_path, commit)` — same inputs ⇒ byte-identical manifest (prompts/tools fingerprinted from source, not runtime).

## Preconditions (checked first; violations are CALLER faults)

1. `repo_path` exists and is a git repository → else `RepoNotFoundError`.
2. `commit` exists in that repo → else `CommitNotFoundError`.
3. Working tree at the resolved checkout is clean (no modified/untracked tracked files) → else `DirtyRepositoryError`.

Instantiation happens inside a WorktreeRunner checkout at `commit` (see `worktree_runner.md`), in a subprocess, so scanning an old commit never pollutes the main process.

## Output reconciliation

1. **Locate the root agent.** Convention: `agent.py` exposing `root_agent`. Path/symbol configurable via `config.py` (`AGENT_ENTRYPOINT`). Not found → `AgentEntrypointNotFound`.
2. **Instantiate** in the worktree subprocess. From the ADK object read: agent tree (sub-agents via `agent.sub_agents`), per-agent model id, and the **raw instruction template before `.format`** (ADK exposes the template; fingerprint that, so two commits with the same template share a `PromptNode`).
3. **AST scan** (Tree-sitter if available, else `ast`) of the agent package for what instantiation cannot give reliably: tool function definitions + signatures + source, registered callbacks/hooks, and which agent references which tool. AGENT2 (`code_explorer`) may assist but the scanner must have a deterministic non-LLM fallback — the manifest must be reproducible without any LLM call.
4. **Merge** into `AgentManifest`; fingerprint prompts (raw template) and tools (normalized source). Reconcile against the agent's existing Kuzu DB: reuse `PromptNode`/`ToolNode` when a fingerprint already exists (do not duplicate).

## Error taxonomy (the blame fence)

`scanner/errors.py`. Every raised error is exactly one category. Unexpected exceptions are wrapped, never leaked as the wrong category.

| Exception | Category | Meaning / who is to blame |
| --- | --- | --- |
| `RepoNotFoundError`, `CommitNotFoundError`, `DirtyRepositoryError` | **CallerError** | The framework was called wrong (bad path / dirty tree). |
| `AgentEntrypointNotFound`, `UnsupportedAgentStructure`, `AgentImportError` | **AgentError** | The agent-under-test is malformed/unsupported. Carries the agent's underlying traceback. |
| `ScannerInternalError` | **FrameworkError** | A bug in the scanner. Wraps any unexpected exception with full context. |

Base class hierarchy:

```python
class ScannerError(Exception): ...
class CallerError(ScannerError): ...        # RepoNotFound, CommitNotFound, DirtyRepository
class AgentError(ScannerError):             # carries .agent_traceback
    def __init__(self, msg, agent_traceback: str | None = None): ...
class FrameworkError(ScannerError): ...      # ScannerInternalError
```

Rule: the top-level `scan` body is wrapped so any exception that is **not** already a `ScannerError` becomes a `FrameworkError`. `AgentImportError` is raised only when the failure is provably inside the agent's own import/instantiation (the subprocess returns a structured failure with the agent's traceback). This is what makes "wrong agent" vs "our bug" testable.

## Pseudocode

```python
def scan(repo_path: Path, commit: str) -> AgentManifest:
    try:
        _check_repo(repo_path)               # -> RepoNotFoundError
        _check_commit(repo_path, commit)     # -> CommitNotFoundError
        with WorktreeRunner(repo_path, commit) as wt:   # -> DirtyRepositoryError if dirty
            entry = resolve_entrypoint(wt.path)          # -> AgentEntrypointNotFound
            inst = wt.run_introspection(entry)           # subprocess; structured result
            if inst.failed:
                raise AgentImportError(inst.message, agent_traceback=inst.traceback)
            ast_info = ast_scan(wt.path / entry.package) # tools, hooks, refs (no LLM)
            manifest = reconcile(inst, ast_info)         # -> UnsupportedAgentStructure if shapes conflict
            fingerprint_prompts_and_tools(manifest)
            return manifest
    except ScannerError:
        raise
    except Exception as e:
        raise ScannerInternalError(f"scan({repo_path}@{commit}) failed unexpectedly") from e
```

`wt.run_introspection` runs a tiny script in the worktree venv that imports the entrypoint and prints JSON: `{agents, models, raw_prompts, subagent_edges}` or `{failed: true, message, traceback}`. The parent never imports agent code.

## Tests (`tests/test_scanner.py` + `tests/fixtures/agents/`)

Fixtures are tiny ADK agents committed into the fixture repos:
- `good_single/` — one agent, one tool, one prompt. Assert manifest equals a stored golden JSON.
- `good_multi/` — root + two sub-agents, shared prompt across two. Assert edges + prompt dedup (same fingerprint).
- `missing_entrypoint/` — no `root_agent` → expect `AgentEntrypointNotFound` (AgentError).
- `import_boom/` — raises on import → expect `AgentImportError` carrying the agent traceback (AgentError).
- `unsupported/` — a structure the reconciler can't map → `UnsupportedAgentStructure` (AgentError).
- dirty tree → `DirtyRepositoryError` (CallerError); bad path → `RepoNotFoundError`; bad sha → `CommitNotFoundError`.
- determinism: `scan()` twice on the same commit ⇒ identical manifest.
- blame test: monkeypatch the reconciler to raise a random `ValueError` ⇒ surfaces as `FrameworkError`, **not** `AgentError`.

Definition of done: every row of the error-taxonomy table has a passing test, and the two golden manifests match.
