import base64

from src.eval_workbench.runner.message_parts import build_genai_parts


def test_build_text_part():
    parts, trace_part = build_genai_parts({"role": "user", "kind": "text", "text": "Hello"})
    assert len(parts) == 1
    assert trace_part["kind"] == "text"
    assert trace_part["text"] == "Hello"


def test_build_media_part_from_user_media_role():
    payload = b"\x89PNG\r\n"
    encoded = base64.b64encode(payload).decode("ascii")
    parts, trace_part = build_genai_parts(
        {
            "role": "user_media",
            "media_mime": "image/png",
            "media_base64": encoded,
            "text": "eiffel_tap.png",
        }
    )
    assert len(parts) == 1
    assert trace_part["kind"] == "media"
    assert trace_part["media_mime"] == "image/png"
    assert parts[0].inline_data.mime_type == "image/png"
    assert parts[0].inline_data.data == payload


def test_multimodal_user_turn_is_multiple_genai_parts():
    """One ADK user Content may contain separate text and inline_data parts."""
    encoded = base64.b64encode(b"\x89PNG\r\n").decode("ascii")
    text_parts, _ = build_genai_parts({"role": "user", "kind": "text", "text": "Afternoon there, $30"})
    media_parts, _ = build_genai_parts(
        {"role": "user_media", "media_mime": "image/png", "media_base64": encoded, "text": "eiffel.png"}
    )
    combined = text_parts + media_parts
    assert len(combined) == 2
    assert combined[0].text == "Afternoon there, $30"
    assert combined[1].inline_data.mime_type == "image/png"
