"""Filesystem layout for per-repo eval artifacts inside the agent-under-test repo."""

from __future__ import annotations

import os
from pathlib import Path

EVAL_FRAMEWORK_DIR = "eval_framework"
EXTRACTORS_DIR = "extractors"
MOCKED_TOOLS_DIR = "mocked_tools"
DB_FILENAME = "eval.kuzu"


def eval_framework_root(repo_path: str | Path) -> Path:
    root = Path(repo_path).resolve() / EVAL_FRAMEWORK_DIR
    root.mkdir(parents=True, exist_ok=True)
    return root


def db_path(repo_path: str | Path) -> str:
    return str(eval_framework_root(repo_path) / DB_FILENAME)


def extractor_source_path(repo_path: str | Path, extractor_id: str) -> Path:
    directory = eval_framework_root(repo_path) / EXTRACTORS_DIR
    directory.mkdir(parents=True, exist_ok=True)
    return directory / f"{extractor_id}.py"


def sanitize_agent_path(agent_path: str) -> str:
    """e.g. a_single_agent.day_trip:root_agent -> a_single_agent_day_trip_root_agent"""
    if ":" in agent_path:
        module, var = agent_path.split(":", 1)
    else:
        module, var = agent_path, "root"
    combined = f"{module}_{var}".replace(".", "_").replace("/", "_").replace("\\", "_")
    return "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in combined)


def mocked_tools_path(repo_path: str | Path, agent_path: str) -> Path:
    directory = eval_framework_root(repo_path) / MOCKED_TOOLS_DIR
    directory.mkdir(parents=True, exist_ok=True)
    return directory / f"{sanitize_agent_path(agent_path)}.py"


def worktree_cache_dir() -> Path:
    cache = Path(os.getenv("EVAL_WT_CACHE", "./data/wt_cache")).resolve()
    cache.mkdir(parents=True, exist_ok=True)
    return cache
