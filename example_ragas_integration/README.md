# RAGAS integration examples

We may need to import metrics from other libraries — for example from the [`ragas`](https://github.com/vibrantlabsai/ragas) package — into the eval workbench / ADK eval pipeline.

Two approaches are sketched here:

## 1. `scenario1_autotranslate/` — skill-based metric translation

Automate the translation from a **Ragas metric** to an **ADK custom metric** (Python scorer + `EvalConfig` wiring) using a SKILL file (`ragas-metric-to-adk`).

This path relies on a **frontier-tier model** to read Ragas source and emit equivalent ADK eval artifacts. The model needs the searchable full source of ragas and the ADK to succeed.

## 2. `scenario2_compat_layer/` — runtime compatibility layer

Keep Ragas metrics as-is and bridge the runtimes:

- Map `google.genai` types (`Part`, `Content`) to Ragas’s message format (`adk_to_ragas.py`).
- Provide **`ADKRagasLLM`**: an ADK-backed implementation of Ragas’s LLM interface so Ragas judge calls run through a minimal ADK agent with structured output.

Use this when you want to **run existing Ragas metrics** without rewriting them, at the cost of maintaining the shim.
