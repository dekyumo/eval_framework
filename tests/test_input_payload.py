from pydantic import BaseModel

from src.eval_workbench.runner.case_input import (
    build_structured_input_message,
    filter_input_payload,
    structured_input_trace_part,
)


class TripInput(BaseModel):
    destination: str
    budget: float | None = None


class _AgentWithSchema:
    input_schema = TripInput


def test_filter_input_payload_strips_unknown_keys():
    agent = _AgentWithSchema()
    result = filter_input_payload(
        agent,
        {"destination": "Acapulco", "extra": "ignored", "budget": 100.0},
    )
    assert result == {"destination": "Acapulco", "budget": 100.0}
    assert "extra" not in result


def test_filter_input_payload_requires_schema_fields():
    agent = _AgentWithSchema()
    try:
        filter_input_payload(agent, {"budget": 50.0})
    except ValueError as exc:
        assert "input_schema" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_filter_input_payload_passthrough_without_schema():
    class _PlainAgent:
        pass

    payload = {"destination": "Paris", "user:name": "John"}
    assert filter_input_payload(_PlainAgent(), payload) == payload


def test_build_structured_input_message_json():
    payload = {"destination": "Acapulco"}
    message = build_structured_input_message(payload)
    assert message.role == "user"
    assert message.parts[0].text == '{"destination": "Acapulco"}'


def test_structured_input_trace_part():
    payload = {"destination": "Acapulco"}
    part = structured_input_trace_part(payload)
    assert part["role"] == "user"
    assert part["kind"] == "text"
    assert '"destination"' in part["text"]
