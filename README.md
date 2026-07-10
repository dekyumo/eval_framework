# Eval Workbench

**Agent Evaluation and Provenance Workbench** — a Python framework for evaluating [Google ADK](https://google.github.io/adk-docs/) agents.

This is a **pre-deployment evaluation tool**, not a production observability platform.

## Features

- **Agent scanning** — introspect ADK agents (object graph, AST, tools/callbacks) and capture immutable snapshots at a commit
- **Eval case management** — define datasets, cases, tags, session state, and optional tool-fault injection
- **Trace generation** — run agents in isolated git worktrees against cases
- **Scoring** — evaluate traces with rubrics, extraction functions, and ground truth
- **Campaigns & IRT** — response matrices and item-response analysis across cases and snapshots
- **Human evaluation** — collect human judgements and compare agreement with automated scores
- **Comparison & drift** — diff agent snapshots and track score changes over time
- **Headless CLI** — run benchmarks without the web UI for CI and scripting

## Architecture

| Layer | Stack |
|-------|-------|
| Backend | Python, Flask, Pydantic |
| Storage | [Kuzu](https://kuzudb.com/) graph database |
| Frontend | React, Vite, Tailwind (static build served by Flask) |
| Agents | Google ADK (scanner, case writer, extractor author, fault mocker, chat operator) |

```
run_app.py  →  Flask API  →  Kuzu DB
                    ↓
              React SPA (compiled to web/static/)
                    ↓
         Git worktrees  →  ADK agent execution  →  traces  →  scoring
```

## Prerequisites

- Python 3.10+
- Git
- Node.js (for frontend development and e2e tests)
- A [Gemini API key](https://aistudio.google.com/apikey) for ADK agent runs

## Installation

```bash
# Clone and enter the project
cd eval_framework

# Install the Python package (editable)
pip install -e ".[dev]"

# Copy environment template and set your API key
cp .env.example .env
# Edit .env and set GEMINI_API_KEY=...

# Optional: clone the tutorial agent repo used by tests and examples
git clone https://github.com/cuppibla/adk_tutorial.git adk_tutorial
```

### Frontend (development only)

The production UI is pre-built under `src/eval_workbench/web/static/`. To rebuild after frontend changes:

```bash
cd src/eval_workbench/frontend
npm install
npm run build
```

## Usage

### Web UI

Point the workbench at a target git repository containing your ADK agent:

```bash
python run_app.py .\adk_tutorial
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000).

Typical workflow:

1. **Onboarding** — scan the agent repo and create a snapshot at a commit
2. **Registries** — define datasets, tags, rubrics, and extraction functions
3. **Cases** — author evaluation cases (inputs, expected behavior, metrics)
4. **Runs** — execute the agent against cases and collect traces
5. **Evals** — score traces and review results
6. **Compare** — diff two snapshots (prompts, tools, topology)
7. **Campaigns** — run IRT-style evaluation campaigns across snapshots
8. **Human Eval** — submit and review human judgements

### Headless CLI

Run a benchmark without starting the web server:

```bash
python run_app.py .\adk_tutorial --mode headless `
  --agent_path "a_single_agent.day_trip:root_agent" `
  --commit HEAD `
  --dataset "DayTrip Tests"
```

Contains an AGENTS.md to help autonomous agents understand the source.
