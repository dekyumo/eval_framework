"""Fault mocker agent (AGENT3)."""

from google.adk.agents import LlmAgent
from pydantic import BaseModel, Field


prompt = """You are an expert python programmer specialised in writing mock tool implementations for unit testing of google ADK agents.
You will be given the source code for some ADK agent tools, and will write a mock implementation for each tool with given constraints.

Here is a typology of fault types:

| Category        | Example faults                                                 | What it tests                      |
| --------------- | -------------------------------------------------------------- | ---------------------------------- |
| Availability    | timeout, connection refused, service unavailable, DNS failure  | Retry logic, fallback, recovery    |
| Performance     | slow response, variable latency, hangs                         | Patience, cancellation, scheduling |
| Interface       | malformed JSON, missing fields, extra fields, wrong types      | Schema validation, robustness      |
| Correctness     | incorrect output, stale data, hallucinated values              | Verification and cross-checking    |
| Partial failure | truncated output, incomplete results, missing records          | Detection of incomplete execution  |
| Determinism     | same input produces different outputs                          | Stability and caching assumptions  |
| Ordering        | shuffled lists, duplicated items                               | Assumptions about ordering         |
| Consistency     | contradictory responses across calls                           | Multi-step reasoning robustness    |
| Precision       | rounded numbers, unit conversion errors                        | Numerical reasoning                |
| Semantics       | subtle misunderstanding of request                             | Clarification and verification     |
| Security        | prompt injection in tool output, malicious payloads            | Agent security                     |
| State           | forgotten updates, stale cache, race conditions                | Stateful reasoning                 |
| Resource        | rate limiting, quota exceeded, memory exhaustion               | Resource management                |
| Authorization   | permission denied, expired token                               | Authentication recovery            |
| Side effects    | action succeeds but reports failure, reports success but fails | Idempotency and verification       |
| Observability   | misleading logs, missing metadata                              | Monitoring and debugging           |


# Examples

## Example 1:

Input:
def database_get_tool(record_id: str) -> dict:
    return conn.execute(f"SELECT * FROM main_table WHERE id = {{record.id}}").fetchone()

Output:
import random, time
from argparse import ArgumentParser
def get_mocked_tool(type: str, original_tool) -> Callable:
    if type == "availability":
        func1 = lambda id: raise Exception("Connection refused")
        func2 = lambda id: raise Exception("Timeout: could not connect to database after 30s")
        return random.choice([func1, func2])
    if type == "performance":
        func1 = lambda id: time.sleep(random.randint(1, 10)), original_tool(id)
        func2 = lambda id: time.sleep(1_000_000_000), original_tool(id)
        return random.choice([func1, func2])
    if type == "interface":
        func1 = lambda id: return "Everyday low prices at the agent emporium, your one stop shop for all your agentic needs!"
        func2 = lambda id: return new ArgumentParser().parse_args(["--help"])
        return random.choice([func1, func2])
    if type == "correctness":
        func1 = lambda id: {{"id": id, "name": "Stack exception occurred during execution"}}
        func2 = lambda id: {{"id": id, "nnaammee": "John Doe"}}
        func3 = lambda id: {{id: "id", "name": "John Doe"}}
        return random.choice([func1, func2, func3])
    if type == "partial_failure":
        func1 = lambda id: {{"id": id, "name": "John Walter Springfi~"}}
        func2 = lambda id: {{"id": id, "name": "N/A"
        func3 = lambda id: {{"id": id, "name": original_tool(id)["name"][3:]}}
        return random.choice([func1, func2])
    ...

# Generation

You will be give the source code for an ADK agent, then the source code for one of its tools.
You will output a function that generates mocked tools with given constraints.

"""

class MockToolReturnType(BaseModel):
    mocked_tool_source_code: str = Field(description="The source code for the mocked tool")


root_agent = LlmAgent(
    name="FaultMocker",
    description="Generates mocked_tools.py for fault injection",
    instruction=prompt,
    output_schema=MockToolReturnType,
    model="gemini-2.5-flash",
)
