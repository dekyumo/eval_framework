# Eval Workbench

**Agent Evaluation and Provenance Workbench** — a Python framework for evaluating [Google ADK](https://google.github.io/adk-docs/) agents with reproducible snapshots, structured test cases, automated scoring, and human-in-the-loop review.

Eval Workbench helps you snapshot an ADK agent at a specific git commit, run it against curated evaluation cases, score traces with rubrics or extraction functions, compare versions over time, and track lineage across prompts, models, tools, and agent topology.

This is a **pre-deployment evaluation tool**, not a production observability platform.

## Features

- **Agent scanning** — introspect ADK agents (object graph, AST, tools/callbacks) and capture immutable snapshots at a commit
- **Eval case management** — define datasets, cases, tags, session state, and optional tool-fault injection
- **Trace generation** — run agents in isolated git worktrees against cases
- **Scoring** — evaluate traces with rubrics, extraction functions, and ground truth
- **Campaigns & IRT** — response matrices and item-response analysis across cases and snapshots
- **Human evaluation** — collect human judgements and compare agreement with automated scores
- **Comparison & drift** — diff agent snapshots and track score changes over time
- **Chat operator** — ADK-powered assistant with access to workbench operations
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
python run_app.py .\adk_tutorial --headless `
  --agent_path "a_single_agent.day_trip:root_agent" `
  --commit HEAD `
  --dataset "DayTrip Tests"
```

Optional flags:

| Flag | Description |
|------|-------------|
| `--tags` | Filter cases by tag |
| `--model` | Model ID for trace generation (default: `gemini-2.5-flash`) |
| `--host`, `--port` | Server bind address (web mode only) |

## Testing

### Python unit tests

```bash
pytest
```

### Frontend end-to-end tests

Requires the `adk_tutorial` repo and a running backend. From the frontend directory:

```bash
cd src/eval_workbench/frontend
npx playwright test tests/e2e.spec.ts
```

## Project layout

```
eval_framework/
├── run_app.py              # Entry point (web UI or headless)
├── pyproject.toml
├── specs/                  # Functional spec, design docs, SOUL principles
├── src/eval_workbench/
│   ├── agents/             # ADK service agents (scanner, case writer, …)
│   ├── analysis/           # Metrics, IRT, agreement, drift, validity
│   ├── domain/             # Pydantic domain models
│   ├── frontend/           # React/Vite source
│   ├── runner/             # Git worktree isolation and agent execution
│   ├── scanner/            # ADK agent introspection
│   ├── services/           # Business logic
│   ├── storage/            # Kuzu schema and repositories
│   └── web/                # Flask app and API routes
└── tests/                  # Backend unit tests
```

See [`codebase.md`](codebase.md) for a detailed file tree and [`specs/functional_spec.md`](specs/functional_spec.md) for the full product specification.

## Design principles

Evaluation is treated as a scientific process:

- **Reproducibility** — agents are versioned artifacts pinned to git commits
- **Explicit versioning** — models, prompts, tools, and topology are tracked in snapshots
- **Train/test separation** — validity checks guard against overfitting to eval cases
- **Inspectable representations** — traces, rubrics, and extractors are visible and editable

The `specs/spec_of_the_spec/SOUL*.md` documents describe the underlying evaluation methodology (TEVV, IRT, fault injection, human-in-the-loop, governance, and more).

## License

*(Add your license here.)*
