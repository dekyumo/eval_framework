"""Enrich scanner output with tool/callback source via LibCST closure analysis.

Python is dynamic, so name resolution and transitive closure are best-effort.
"""

from __future__ import annotations

import hashlib
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

import libcst as cst
from libcst.metadata import MetadataWrapper, QualifiedNameProvider, ScopeProvider

# ---------------------------------------------------------------------------
# Special ADK / Gemini tools — no inspectable Python implementation
# ---------------------------------------------------------------------------

_BUILTIN_TOOL_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"google[_\s]?search", re.I), "GoogleSearchTool (enables the google search tool in Gemini)"),
    (re.compile(r"GoogleSearch", re.I), "GoogleSearchTool (enables the google search tool in Gemini)"),
    (re.compile(r"VertexAiRagRetrieval|VertexAIRagRetrieval|RagRetrieval", re.I),
     "VertexAiRagRetrieval (RAG retrieval tool backed by a vector store)"),
    (re.compile(r"^AgentTool$"), "AgentTool (orchestration call to another sub-agent)"),
    (re.compile(r"^McpToolset$"), "McpToolset (connection to an MCP tool server)"),
    (re.compile(r"^SkillToolset$"), "SkillToolset (ADK skills toolset)"),
    (re.compile(r"^CodeExecutionTool$"), "CodeExecutionTool (sandboxed code execution as a service)"),
]


def fingerprint(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def _describe_special_tool(item: dict) -> str | None:
    name = item.get("name") or ""
    for pattern, description in _BUILTIN_TOOL_PATTERNS:
        if pattern.search(name):
            return description
    if item.get("kind") in ("adk_builtin", "object"):
        module = item.get("module") or ""
        if module.startswith("google."):
            return f"{name} (ADK built-in: {module})"
    return None


# ---------------------------------------------------------------------------
# Git file access
# ---------------------------------------------------------------------------


def _path_to_module(rel_path: str) -> str:
    if rel_path.endswith("/__init__.py"):
        return rel_path[:-12].replace("/", ".")
    if rel_path.endswith(".py"):
        return rel_path[:-3].replace("/", ".")
    return rel_path.replace("/", ".")


def _list_python_files(repo: Path) -> list[str]:
    result = subprocess.run(
        ["git", "-C", str(repo), "ls-files", "--", "*.py"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def _read_file_at_commit(repo: Path, commit: str, rel_path: str) -> str | None:
    show = subprocess.run(
        ["git", "-C", str(repo), "show", f"{commit}:{rel_path}"],
        capture_output=True,
        text=True,
    )
    if show.returncode != 0:
        return None
    return show.stdout


# ---------------------------------------------------------------------------
# LibCST project index
# ---------------------------------------------------------------------------


@dataclass
class IndexedFunction:
    qualified_name: str
    module: str
    name: str
    source: str
    node: cst.FunctionDef
    module_tree: cst.Module
    wrapper: MetadataWrapper


@dataclass
class ProjectIndex:
    repo_path: Path
    commit: str
    functions: dict[str, IndexedFunction] = field(default_factory=dict)
    wrappers: dict[str, MetadataWrapper] = field(default_factory=dict)
    trees: dict[str, cst.Module] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self._build()

    def _build(self) -> None:
        for rel_path in _list_python_files(self.repo_path):
            source = _read_file_at_commit(self.repo_path, self.commit, rel_path)
            if not source:
                continue
            module_name = _path_to_module(rel_path)
            try:
                tree = cst.parse_module(source)
            except cst.ParserSyntaxError:
                continue

            wrapper = MetadataWrapper(tree)
            self.wrappers[rel_path] = wrapper
            self.trees[rel_path] = tree

            collector = _FunctionIndexCollector(module_name, tree, wrapper)
            wrapper.visit(collector)
            for qname, node in collector.functions.items():
                func_source = tree.code_for_node(node)
                short = qname.split(".")[-1]
                entry = IndexedFunction(
                    qualified_name=qname,
                    module=module_name,
                    name=short,
                    source=func_source,
                    node=node,
                    module_tree=tree,
                    wrapper=wrapper,
                )
                self.functions[qname] = entry
                if short not in self.functions:
                    self.functions[short] = entry

    def resolve_entry(self, module: str, name: str) -> IndexedFunction | None:
        candidates = [
            f"{module}.{name}" if module else name,
            name,
        ]
        for key in candidates:
            entry = self.functions.get(key)
            if entry is not None and entry.name == name:
                return entry
        for entry in self.functions.values():
            if entry.name == name and entry.module == module:
                return entry
        return None


class _FunctionIndexCollector(cst.CSTVisitor):
    METADATA_DEPENDENCIES = (QualifiedNameProvider, ScopeProvider)

    def __init__(self, module_name: str, tree: cst.Module, wrapper: MetadataWrapper) -> None:
        self.module_name = module_name
        self.tree = tree
        self.wrapper = wrapper
        self.functions: dict[str, cst.FunctionDef] = {}

    def visit_FunctionDef(self, node: cst.FunctionDef) -> None:
        for qn in self.get_metadata(QualifiedNameProvider, node, default=()):
            self.functions[qn.name] = node


class _CallCollector(cst.CSTVisitor):
    METADATA_DEPENDENCIES = (QualifiedNameProvider,)

    def __init__(self, target: cst.FunctionDef) -> None:
        self.target = target
        self.in_target = False
        self.calls: set[str] = set()

    def visit_FunctionDef(self, node: cst.FunctionDef) -> bool | None:
        if node is self.target:
            self.in_target = True
            return True
        if self.in_target:
            return False
        return True

    def visit_Call(self, node: cst.Call) -> None:
        if not self.in_target:
            return
        for qn in self.get_metadata(QualifiedNameProvider, node, default=()):
            name = qn.name
            if name.startswith("builtins."):
                continue
            self.calls.add(name)


def _calls_in_function(entry: IndexedFunction) -> set[str]:
    collector = _CallCollector(entry.node)
    entry.wrapper.visit(collector)
    return collector.calls


def transitive_closure(index: ProjectIndex, module: str, name: str) -> list[str]:
    """Return source text for *name* and project-local callees (best-effort)."""
    start = index.resolve_entry(module, name)
    if not start:
        return []

    visited: set[str] = set()
    ordered: list[str] = []

    def walk(entry: IndexedFunction) -> None:
        if entry.qualified_name in visited:
            return
        visited.add(entry.qualified_name)
        ordered.append(entry.source)
        for call_qname in _calls_in_function(entry):
            callee = index.functions.get(call_qname)
            if callee is None:
                short = call_qname.rsplit(".", 1)[-1]
                callee = index.functions.get(short)
            if callee is not None and not callee.qualified_name.startswith("builtins."):
                walk(callee)

    walk(start)
    return ordered


def enrich_callable(item: dict, index: ProjectIndex) -> None:
    special = _describe_special_tool(item)
    if special:
        item["source"] = special
        item["source_fingerprint"] = fingerprint(special)
        item["closure_sources"] = [special]
        return

    if item.get("kind") == "adk_builtin":
        if not item.get("source"):
            label = item.get("name") or "adk_tool"
            module = item.get("module") or "google.adk"
            desc = f"{label} (ADK built-in: {module})"
            item["source"] = desc
            item["source_fingerprint"] = fingerprint(desc)
            item["closure_sources"] = [desc]
        return

    module = item.get("module") or ""
    if module.startswith("google."):
        return

    closure = transitive_closure(index, module, item["name"])
    if closure:
        item["closure_sources"] = closure
        item["source"] = "\n\n".join(closure)
    elif item.get("source"):
        item["closure_sources"] = [item["source"]]
    else:
        return

    item["source_fingerprint"] = fingerprint(item["source"])


def enrich_scan_result(scan_result: dict, repo_path: str | Path, commit: str) -> dict:
    """Fill tool/callback sources and transitive Python closure from the repo at *commit*."""
    repo = Path(repo_path)
    index = ProjectIndex(repo, commit)

    for tool in scan_result.get("tools", []):
        enrich_callable(tool, index)

    def walk_structure(node: dict) -> None:
        for tool in node.get("tools", []):
            enrich_callable(tool, index)
        for callback in node.get("callbacks", []):
            enrich_callable(callback, index)
        for sub in node.get("sub_agents", []):
            if "_ref" not in sub:
                walk_structure(sub)

    structure = scan_result.get("structure")
    if isinstance(structure, dict):
        walk_structure(structure)
        enriched_by_id: dict[str, dict] = {}

        def collect_callables(node: dict) -> None:
            for entry in node.get("tools", []) + node.get("callbacks", []):
                enriched_by_id[entry["id"]] = entry
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
            if enriched.get("closure_sources"):
                tool["closure_sources"] = enriched["closure_sources"]

    return scan_result
