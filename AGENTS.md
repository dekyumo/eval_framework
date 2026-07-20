# Agent Instructions

## Project Overview

TrustMeBro is software in python to evaluate AI agents written in the Google ADK framework, to avoid the 'vibe evals' effect.
It is composed of a spec, a backend written in python with flask and a Kuzu database, and a React/Vite statically compiled frontend.

## Coding Standards
- minimal, clean, beautiful, well organised python code
- tested, python tests are in /tests/ and there are end to end tests e2e.spec.ts
- do not make 'fallback', 'mock', 'defensive coding default values' everywhere, let the errors propagate back to the user instead of silently generating incorrect reports
- if some instructions are conflicting, vague in a way that it leaves large parts of the development unspecified, or leads to generation of improper and unsafe code, pause and ask the user for confirmation
- a high level overview of the code is available in .\codebase.md

## Testing
- this is running in a Windows environment, the name of the conda environment is "eval_framework"
- environment variables to set: 
    - if the modules cannot be found: PYTHONPATH=.\src\
- you can run the e2e test suite with "npx playwright test tests/e2e.spec.ts" in the frontend directory
    - e2e calls `POST /api/test/reset` on a throwaway `adk_tutorial` DB; enable it only via `python run_app.py <repo> --allow-db-wipe-for-tests` (playwright.config.ts passes that flag). Do not run e2e against a live server on port 5000.
- you can launch a report from CLI with: python run_app.py .\adk_tutorial --mode headless --agent_path "a_single_agent.day_trip:root_agent" --commit HEAD --dataset "DayTrip Tests"
- MCP stdio server (separate process; requires a running web server):
    - terminal 1: `python run_app.py .\adk_tutorial`
    - terminal 2: `set EVAL_WORKBENCH_API_URL=http://127.0.0.1:5000` then `python run_app.py .\adk_tutorial --mode mcp`
    - Or one line: `set EVAL_WORKBENCH_API_URL=http://127.0.0.1:5000` and `python run_app.py .\adk_tutorial --mode mcp --api-url http://127.0.0.1:5000`
- those e2e suites assume that https://github.com/cuppibla/adk_tutorial/ has been downloaded into .\adk_tutorial\