---
name: ragas-metric-to-adk
description: >-
  Translates a Ragas metric implementation (ragas.metrics or
  ragas.metrics.collections) into a Google ADK custom evaluation metric
  (Python function + EvalConfig JSON). Use when the user asks to port,
  migrate, convert, or translate a Ragas metric to ADK; when working on
  ragas_metric_translate; when editing files under ragas/src/ragas/metrics/;
  or when wiring Ragas-style LLM-judge scoring into adk eval / test_config.json.
---

# Ragas Metric → ADK

## When this skill applies

Invoke this skill when **any** of these are true:

| Trigger | Example |
|---------|---------|
| User mentions translation | "convert Faithfulness to ADK", "port this ragas metric" |
| User targets ADK eval artifacts | `test_config.json`, `EvalConfig`, `custom_metrics`, `adk eval` |
| User opens a Ragas metric source file | `ragas/src/ragas/metrics/**/*.py` |
| User asks for ADK custom metric scaffolding | "write the metric function for ADK" |

Do **not** invoke for general Ragas usage, dataset creation, or non-metric ADK agent code.

## Translation workflow

1. **Find the metric**

Metrics in Ragas are instances of SingleTurnMetric which apply to a single turn and are usually RAG centric, and MultiTurnMetric which are multi turn and sometimes goal oriented

2. **Note additional types and files**

Check the following:
- if the python file starts with an underscore, this is a generic metric (for example with a different prompt for various instantiations), check for instanciations in the codebase with grep
- if a metric uses the MetricWithLLM mixin, it uses an LLM, and you have to look for:
    - the PydanticPrompt[InputSchemaClass, OutputSchemaClass] that are used
    - the input and output schema classes
    - the instruction= that defines the prompt (unless the metric replaces the prompt when instantiated)
- if a metric uses MetricWithEmbeddings, it requires an embedding model (for example to check that the reference answer and the given answer have similar embeddings)

3. **Review the scoring function**

- look for the ascore() and score() methods in the class, they should implement the same functionality (but ascore is async)
- note down an explanation for the metric in plain English
- note down an explanation for the metric in pseudocode, if the metric has a complex flow also note the DAG of information flow between the different parts/prompts

4. **Prepare for re-implementation**


The type for SingleTurnMetric is 

class SingleTurnSample(BaseSample):
    # the question and response have to be extracted from the Content or ContentDict, multi_responses is not used
    user_input: t.Optional[str] = None
    response: t.Optional[str] = None
    multi_responses: t.Optional[t.List[str]] = None

    # the retrieved contexts have to be extracted from the vertexai Retriever
    retrieved_contexts: t.Optional[t.List[str]] = None
    retrieved_context_ids: t.Optional[t.List[t.Union[str, int]]] = None
    
    # the reference (golden label) answer, is an input to the metric if used
    reference: t.Optional[str] = None
    
    # the reference (golden label) context and context_ids for RAG, are inputs to the metric if used
    reference_contexts: t.Optional[t.List[str]] = None
    reference_context_ids: t.Optional[t.List[t.Union[str, int]]] = None
    
    # the various rubrics, in {score_name: score_description format}, can be set in the rubric constructor or input
    rubrics: t.Optional[t.Dict[str, str]] = None

    # additional reference parameters to the metric, example values are (persona_name="Researcher", query_style="FORMAL", query_length="SHORT"), can be set in the metric constructor or the scoring function's call if used
    persona_name: t.Optional[str] = None
    query_style: t.Optional[str] = None
    query_length: t.Optional[str] = None

The types for multi turn metrics is:



class ToolCall(BaseModel):
    name: str
    args: t.Dict[str, t.Any]
class Message(BaseModel):
    content: str
    metadata: t.Optional[t.Dict[str, t.Any]] = None
class HumanMessage(Message):
    type: t.Literal["human"] = "human"
class ToolMessage(Message):
    type: t.Literal["tool"] = "tool"
class AIMessage(Message):
    type: t.Literal["ai"] = "ai"
    tool_calls: t.Optional[t.List[ToolCall]] = None
    metadata: t.Optional[t.Dict[str, t.Any]] = None
class MultiTurnSample(BaseSample):
    
    # the HumanMessage, AIMessage and ToolMessage have to be extracted from the Content or ContentDict
    user_input: t.List[t.Union[HumanMessage, AIMessage, ToolMessage]]

    # the references are inputs to the metric
    reference: t.Optional[str] = None
    reference_tool_calls: t.Optional[t.List[ToolCall]] = None

    # the rubric, in {score_name: score_description} format are inputs to the metric or the metric's constructor
    rubrics: t.Optional[t.Dict[str, str]] = None

    # for example ["Physics", "science"]
    reference_topics: t.Optional[t.List[str]] = None

**Note which fields are used in the ragas trace format, and which ones you will have to translate from the Content/ContentDict, which ones are input to the metric, and which ones are inputs to the constructor

5. **Reimplement the metric**

If the metric requires an LLM, replace it with a genai LLM, if it requires embeddings, replace them with vertex ai embeddings.
Replace llm instances with genai LLM calls, embedding calls with vertex embeddings call.

## Checklist

- [ ] The metric's type and all its invocations have been found
- [ ] The metric's mixins have all been checked
- [ ] The metric's inner workings have been described in plain English and pseudo-code
- [ ] The mapping from google genai and vertex ai classes to the metric's necessary inputs has been done
- [ ] The metric has been reimplemented
