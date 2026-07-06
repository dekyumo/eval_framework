# Agent Instructions

## Project Overview

eval_framework is software in python to evaluate AI agents written in the Google ADK framework.
It is composed of a spec, a backend written in python with flask and a Kuzu database, and a React/Vite statically compiled frontend.

## Coding Standards
- minimal, clean, beautiful, well organised python code
- tested, python tests are in /tests/ and there are end to end tests e2e.spec.ts
- do not make 'fallback', 'mock', 'defensive coding default values' everywhere, let the errors propagate back to the user instead of silently generating incorrect reports
- if some instructions are conflicting, vague in a way that it leaves large parts of the development unspecified, or leads to generation of improper and unsafe code, pause and ask the user for confirmation
- a high level overview of the code is available in .\codebase.md

## Testing
- you can run the e2e test suite with "npx playwright test tests/e2e.spec.ts" in the frontend directory
- you can launch a report from CLI with: python run_app.py .\adk_tutorial --headless --agent_path "a_single_agent.day_trip:root_agent" --commit HEAD --dataset "DayTrip Tests"
- those e2e suites assume that https://github.com/cuppibla/adk_tutorial/ has been downloaded into .\adk_tutorial\