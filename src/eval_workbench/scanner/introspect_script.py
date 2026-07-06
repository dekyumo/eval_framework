"""Subprocess entrypoint: import agent in worktree and dump structure as JSON."""

import importlib
import json
import sys

from src.eval_workbench.scanner.agent_structure_dump import build_scan_result


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit(1)

    mod_name, var_name = sys.argv[1].split(":", 1)
    module = importlib.import_module(mod_name)
    agent = getattr(module, var_name)
    print(json.dumps(build_scan_result(agent)))


if __name__ == "__main__":
    main()
