# Contract: WorktreeRunner (FRAGILE)

`runner/worktree.py`. Provides **run isolation**: every introspection or eval run of a given commit happens in a throwaway git worktree with its own virtual environment, executed in a subprocess. This is a *correctness-under-concurrency* mechanism, **not** a security sandbox (LIVE faults still need real sandboxing — out of scope here).

## Why it exists

Re-running an old commit means checking out that commit and importing the agent's modules. Doing that in the main process or main working tree is unsafe: `sys.modules` collisions across commits, and working-tree corruption under concurrency. So each run gets its own worktree + venv + subprocess.

## Interface

```python
class WorktreeRunner:
    def __init__(self, repo_path: Path, commit: str): ...
    def __enter__(self) -> "Worktree": ...
    def __exit__(self, *exc) -> None: ...     # ALWAYS removes the worktree

class Worktree:
    path: Path                                # the checked-out tree
    python: Path                              # the venv interpreter
    def run_introspection(self, entry) -> IntrospectionResult: ...
    def run_case(self, snapshot, case, model_id, fault_config) -> Trace: ...
```

Usage:

```python
with WorktreeRunner(repo_path, commit) as wt:
    trace = wt.run_case(snapshot, case, model_id, fault_config)
```

## Lifecycle

1. **Add worktree.** `git -C <repo> worktree add --detach <tmp_dir> <commit>`. `tmp_dir` is unique (`<cache>/wt/<commit>-<uuid>`).
2. **Provision venv.** `uv venv` in the tree, then `uv pip install` from the agent's lockfile/requirements at that commit. **Cache** venvs keyed by `(commit, lockfile_hash)` and reuse across repetitions and across a campaign's cases — venv creation is the slow step.
3. **Execute in subprocess.** `run_case` invokes `runner/exec_script.py` via `wt.python` as a subprocess. The script imports the entrypoint, applies fault callbacks (see `fault_injector.md`), runs the case conversation, and prints a serialized `Trace` (or a structured failure → a `Trace` with `exception` set; a crash is a scorable trace).
4. **Remove.** In `__exit__` (finally semantics): `git worktree remove --force <tmp_dir>` and delete the dir. On process startup, `git worktree prune` + sweep orphaned `<cache>/wt/*` from crashed runs.

## Concurrency rules

- Each run = its own worktree dir + its own subprocess. Worktrees never shared between concurrent runs.
- Serialize `git worktree add` / `remove` / `prune` with a single process-level lock (`threading.Lock` or a file lock) — git's worktree metadata is not safe under concurrent mutation. The **runs themselves execute fully in parallel**; only the add/remove bookkeeping is serialized.
- Venv cache reads are concurrent; venv *creation* for a given key is guarded so two runs don't build the same venv twice (build-once, then share read-only).

## Known caveats (document and handle)

- **Subprocess, not import.** Never import agent code into the parent. This is the whole point; do not "optimize" it away.
- **Windows (the dev environment is win32).** `git worktree` and `uv` work on Windows, but: paths are long (keep `tmp_dir` short, near the drive root if needed), file locks are mandatory (a venv/file held open by a subprocess blocks `worktree remove` — ensure the subprocess has fully exited before removal), and symlinks may be unavailable (uv must copy, not link). Use `git worktree remove --force` and retry removal a few times with a short backoff on `PermissionError`.
- **Lockfile may be absent.** If the agent repo has no lockfile, fall back to installing `requirements.txt`, else install only ADK + declared deps from `config.py`. Record what was installed in the snapshot's `dependency_lock`.
- **Slow first run.** Surface venv-build time separately from agent latency so it never pollutes the measured `latency_ms` of the trace.
- **Disk.** Worktrees + venvs grow; prune on startup and after each campaign.
- **Determinism boundary.** The worktree guarantees a clean, pinned environment; it cannot make a stochastic model deterministic. That is handled by repetitions + folding (SOUL3/6), not here.

## Pseudocode

```python
class WorktreeRunner:
    def __enter__(self):
        with _GIT_LOCK:
            _ensure_clean(self.repo_path, self.commit)     # -> DirtyRepositoryError
            self.tmp = unique_dir()
            git(self.repo_path, "worktree", "add", "--detach", self.tmp, self.commit)
        self.python = provision_venv(self.tmp, self.commit)  # cached by (commit, lockfile_hash)
        return Worktree(self.tmp, self.python)

    def __exit__(self, *exc):
        for attempt in range(3):                            # Windows file-lock retry
            try:
                with _GIT_LOCK:
                    git(self.repo_path, "worktree", "remove", "--force", self.tmp)
                shutil.rmtree(self.tmp, ignore_errors=True)
                return
            except PermissionError:
                time.sleep(0.2 * (attempt + 1))
```

`exec_script.py` (runs under `wt.python`):

```python
# argv: snapshot.json case.json model_id fault_config.json -> stdout: trace.json
def main():
    agent = import_root_agent(ENTRYPOINT)
    register_fault_callbacks(agent, fault_config)   # no-op if None ; see fault_injector.md
    try:
        parts, structured, tokens, latency = drive_conversation(agent, case, model_id)
        print(Trace(... exception=None ...).model_dump_json())
    except Exception as e:
        print(Trace(... parts=parts_so_far, exception=format_exc() ...).model_dump_json())
```

## Tests (`tests/test_worktree.py`)

- add → tree exists at the right commit; `python` runs; remove → tree gone, `git worktree list` clean.
- run two cases concurrently on the same commit → no collision, two valid traces.
- run cases on two different commits concurrently → correct, independent.
- exception inside `run_case` → worktree still removed (finally), and the failure becomes a `Trace` with `exception` set.
- venv cache hit on the second repetition (no rebuild).
- orphan sweep: pre-create a fake stale worktree dir → startup prune removes it.
