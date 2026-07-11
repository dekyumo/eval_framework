"""subprocess.run with UTF-8 text mode (Windows defaults to cp1252 and breaks on git output)."""

from __future__ import annotations

import subprocess
from typing import Any


def run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
    if kwargs.get("text") or kwargs.get("capture_output"):
        kwargs.setdefault("encoding", "utf-8")
        kwargs.setdefault("errors", "replace")
    return subprocess.run(*args, **kwargs)
