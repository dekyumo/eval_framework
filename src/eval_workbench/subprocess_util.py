"""subprocess.run with UTF-8 text mode (Windows defaults to cp1252 and breaks on git output)."""

from __future__ import annotations

import os
import subprocess
from typing import Any


def run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
    if kwargs.get("text") and kwargs.get("capture_output"):
        kwargs.setdefault("encoding", "utf-8")
        kwargs.setdefault("errors", "replace")
        env = dict(kwargs.get("env") or os.environ)
        env.setdefault("PYTHONIOENCODING", "utf-8")
        kwargs["env"] = env
    return subprocess.run(*args, **kwargs)
