"""Model Context Protocol surface for the eval workbench.

`registry` is the single source of truth mapping tool names to callables; it is
shared by the stdio MCP server (outer loop, driven by an autonomous coding
agent) and the blueprint runner (inner loop, running inside the framework).
"""
