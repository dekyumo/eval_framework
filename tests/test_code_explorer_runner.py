from unittest.mock import patch

import pytest

from src.eval_workbench.agents.code_explorer.agent import CodeExplorerOutput
from src.eval_workbench.scanner.code_explorer_runner import run_code_explorer


def test_run_code_explorer_uses_runner_async_api():
    graph = {
        "root_agent_name": "case_writer",
        "agents": [{"name": "case_writer"}],
        "tools": [],
        "prompts": [],
    }
    expected = CodeExplorerOutput(
        description="Writes eval cases",
        in_distribution=["generate eval cases"],
        out_of_distribution=["deploy to prod"],
        distribution_margin=["generate rubrics"],
    )

    with patch(
        "src.eval_workbench.scanner.code_explorer_runner._run_code_explorer_async",
        return_value=expected,
    ) as run_async:
        result = run_code_explorer(graph)

    assert result == expected
    run_async.assert_awaited_once()
    payload = run_async.await_args.args[0]
    assert "case_writer" in payload
