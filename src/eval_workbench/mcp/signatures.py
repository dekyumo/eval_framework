""" Checks that the MCP function signature and the service function signature are the same
If not, this means that the coding agent forgot to update one of the two"""

from __future__ import annotations

import inspect
from collections.abc import Callable

from src.eval_workbench.mcp.tool_defs import TOOL_NAMES


def assert_matching_signatures(
    reference: dict[str, Callable[..., object]],
    candidate: dict[str, Callable[..., object]],
) -> None:
    """Raise TypeError if any MCP tool signature diverges from the reference registry."""
    for name in TOOL_NAMES:
        if name not in reference or name not in candidate:
            raise TypeError(f"Missing tool {name!r} in registry")
        ref_sig = inspect.signature(reference[name])
        cand_sig = inspect.signature(candidate[name])
        if ref_sig != cand_sig:
            raise TypeError(
                f"MCP tool {name!r} signature mismatch:\n"
                f"  expected: {ref_sig}\n"
                f"  actual:   {cand_sig}"
            )
