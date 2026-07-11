"""Tests for subprocess_util."""

import subprocess

from src.eval_workbench.subprocess_util import run


def test_run_uses_utf8_for_text_capture():
    result = run(
        ["python", "-c", "print('café \\u20ac')"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "café" in result.stdout
