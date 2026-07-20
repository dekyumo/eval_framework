"""Gunicorn entrypoint for container / Cloud Run deployments."""

import os

from src.eval_workbench.web.app import create_app

application = create_app(repo_path=os.environ.get("AGENT_REPO", "/agent"))
