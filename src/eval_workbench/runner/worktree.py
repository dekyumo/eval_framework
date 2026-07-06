import json
import os
import shutil
import subprocess
import threading
import time
import uuid
from pathlib import Path

from src.eval_workbench.scanner.errors import (
    AgentImportError,
    CommitNotFoundError,
    DirtyRepositoryError,
)

_GIT_LOCK = threading.Lock()
_VENV_LOCK = threading.Lock()
_VENV_CACHE: dict[str, Path] = {}


def _framework_root() -> Path:
    return Path(__file__).resolve().parents[3]


class Worktree:
    def __init__(self, path: Path, python: Path):
        self.path = path
        self.python = python

    def run_introspection(self, target_agent_path: str) -> dict:
        introspect_script = Path(__file__).resolve().parents[1] / "scanner" / "introspect_script.py"

        env = os.environ.copy()
        env["PYTHONPATH"] = os.pathsep.join([str(self.path), str(_framework_root())])

        result = subprocess.run(
            [str(self.python), str(introspect_script), target_agent_path],
            cwd=str(self.path),
            env=env,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise AgentImportError(f"Introspection failed: {result.stderr}")

        return json.loads(result.stdout)


class WorktreeRunner:
    def __init__(self, repo_path: str | Path, commit: str):
        self.repo_path = Path(repo_path).absolute()
        self.commit = commit
        self.tmp: Path | None = None

        from src.eval_workbench.repo_layout import worktree_cache_dir
        self.cache_dir = worktree_cache_dir()

    def __enter__(self) -> Worktree:
        with _GIT_LOCK:
            self._ensure_clean()

            uid = uuid.uuid4().hex[:8]
            self.tmp = self.cache_dir / f"wt_{self.commit}_{uid}"

            res = subprocess.run(
                ["git", "-C", str(self.repo_path), "worktree", "add", "--detach", str(self.tmp), self.commit],
                capture_output=True,
                text=True,
            )
            if res.returncode != 0:
                raise RuntimeError(f"git worktree add failed: {res.stderr}")

        import sys
        return Worktree(self.tmp, Path(sys.executable))

    def __exit__(self, *exc) -> None:
        if not self.tmp:
            return

        for attempt in range(3):
            try:
                with _GIT_LOCK:
                    subprocess.run(
                        ["git", "-C", str(self.repo_path), "worktree", "remove", "--force", str(self.tmp)],
                        capture_output=True,
                        text=True,
                    )
                if self.tmp.exists():
                    shutil.rmtree(str(self.tmp), ignore_errors=True)
                return
            except PermissionError:
                time.sleep(0.2 * (attempt + 1))

        if self.tmp.exists():
            shutil.rmtree(str(self.tmp), ignore_errors=True)

    def _ensure_clean(self):
        if not (self.repo_path / ".git").exists() and not (self.repo_path.parent / ".git").exists():
            pass

        res = subprocess.run(
            ["git", "-C", str(self.repo_path), "status", "--porcelain", "-uno"],
            capture_output=True,
            text=True,
        )
        if res.returncode != 0:
            pass
        elif res.stdout.strip():
            raise DirtyRepositoryError(f"Repository {self.repo_path} is dirty.")

        res = subprocess.run(
            ["git", "-C", str(self.repo_path), "rev-parse", "--verify", f"{self.commit}^{{commit}}"],
            capture_output=True,
            text=True,
        )
        if res.returncode != 0:
            raise CommitNotFoundError(f"Commit {self.commit} not found.")

    def _provision_venv(self) -> Path:
        import sys
        return Path(sys.executable)
