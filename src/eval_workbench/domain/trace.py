from typing import Any, Literal
from pydantic import BaseModel

Role = Literal["system", "user", "assistant", "tool"]
PartKind = Literal["text", "tool_call", "tool_response", "media"]

class MessagePart(BaseModel):
    role: Role
    kind: PartKind
    text: str | None = None
    tool_name: str | None = None
    tool_args: dict | None = None          # for tool_call
    tool_response: Any | None = None        # for tool_response
    media_uri: str | None = None            # for media (stored out of band)
    media_mime: str | None = None           # MIME type for inline media (e.g. image/png)
    media_base64: str | None = None         # base64-encoded media bytes for eval case input
    ts: float | None = None                 # optional wall-clock

class TokenUsage(BaseModel):
    prompt: int = 0
    completion: int = 0
    total: int = 0

class Trace(BaseModel):
    id: str
    parts: list[MessagePart]                # the full conversation incl. tool calls/responses
    structured_output: Any | None = None    # final structured result if the agent produced one
    exception: str | None = None            # set iff the agent crashed; a crash IS a scorable trace
    latency_ms: float | None = None
    tokens: TokenUsage | None = None
    # provenance (foreign keys)
    snapshot_id: str
    case_id: str
    model_id: str                            # the model actually used (campaign may override)
    repetition_index: int = 0
    fault_config_id: str | None = None
