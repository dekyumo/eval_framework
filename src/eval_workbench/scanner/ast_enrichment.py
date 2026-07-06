"""Gets the source code of the tools and callbacks from the repository.
Since python code is dynamically executed, this is imperfect."""

from __future__ import annotations

import ast
import hashlib
import subprocess
from pathlib import Path


def fingerprint(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def _module_to_path(module: str) -> str:
    return module.replace(".", "/") + ".py"


def _read_file_at_commit(repo_path: Path, commit: str, rel_path: str) -> str | None:
    result = subprocess.run(
        ["git", "-C", str(repo_path), "show", f"{commit}:{rel_path}"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None
    return result.stdout


def _ast_function_source(file_source: str, func_name: str) -> str | None:
    try:
        tree = ast.parse(file_source)
    except SyntaxError:
        return None

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == func_name:
            segment = ast.get_source_segment(file_source, node)
            return segment or None
    return None


def enrich_scan_result(scan_result: dict, repo_path: str | Path, commit: str) -> dict:
    """Fill missing tool sources from repository files and refresh fingerprints."""
    repo = Path(repo_path)
    file_cache: dict[str, str | None] = {}

    def enrich_callable(item: dict) -> None:
        if item.get("kind") == "adk_builtin":
            return
        if item.get("source"):
            return

        module = item.get("module") or ""
        if not module or module.startswith("google."):
            return

        rel_path = _module_to_path(module)
        if rel_path not in file_cache:
            file_cache[rel_path] = _read_file_at_commit(repo, commit, rel_path)

        file_source = file_cache[rel_path]
        if not file_source:
            return

        ast_source = _ast_function_source(file_source, item["name"])
        if not ast_source:
            return

        item["source"] = ast_source
        item["source_fingerprint"] = fingerprint(ast_source)

    for tool in scan_result.get("tools", []):
        enrich_callable(tool)

    def walk_structure(node: dict) -> None:
        for tool in node.get("tools", []):
            enrich_callable(tool)
        for callback in node.get("callbacks", []):
            enrich_callable(callback)
        for sub in node.get("sub_agents", []):
            if "_ref" not in sub:
                walk_structure(sub)

    structure = scan_result.get("structure")
    if isinstance(structure, dict):
        walk_structure(structure)
        enriched_by_id: dict[str, dict] = {}

        def collect_callables(node: dict) -> None:
            for item in node.get("tools", []) + node.get("callbacks", []):
                enriched_by_id[item["id"]] = item
            for sub in node.get("sub_agents", []):
                if "_ref" not in sub:
                    collect_callables(sub)

        collect_callables(structure)
        for tool in scan_result.get("tools", []):
            enriched = enriched_by_id.get(tool["id"])
            if not enriched:
                continue
            if enriched.get("source"):
                tool["source"] = enriched["source"]
                tool["source_fingerprint"] = enriched["source_fingerprint"]

    return scan_result
