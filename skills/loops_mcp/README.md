# Loop skills — outer loop (autonomous agent via MCP)

From the eval_framework repo root, with the target agent repo as the positional argument:

```bash
python run_app.py <repo> --mode mcp
```

Register the server in your MCP client (Cursor, Claude Code, Codex, etc.) as a
stdio process. All tools share the registry in `mcp/registry.py`.

The standalone `python -m src.eval_workbench.mcp` entry point remains available
but `run_app.py --mode mcp` is preferred — it passes the repo path explicitly.
