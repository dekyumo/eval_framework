import pytest
from pathlib import Path
from src.eval_workbench.runner.worktree import WorktreeRunner
from src.eval_workbench.scanner.errors import DirtyRepositoryError, CommitNotFoundError
import subprocess

def test_worktree_clean(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=str(repo), check=True)
    (repo / "test.txt").write_text("hello")
    subprocess.run(["git", "add", "."], cwd=str(repo), check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=str(repo), check=True)
    
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(repo), capture_output=True, text=True).stdout.strip()
    
    with WorktreeRunner(repo, commit) as wt:
        assert wt.path.exists()
        assert wt.python.exists()
        tmp_path_check = wt.path
    
    # After exit, it should be removed
    assert not tmp_path_check.exists()
