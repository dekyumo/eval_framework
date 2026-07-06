"""Build google-genai message parts from eval case conversation turns."""

from __future__ import annotations

import base64
import mimetypes

from google.genai import types


def build_genai_parts(message: dict) -> tuple[list[types.Part], dict]:
    """Return genai Parts and a trace-part dict for one conversation turn."""
    role = message.get("role", "user")
    kind = message.get("kind", "text")

    if role == "user_media":
        kind = "media"
        role = "user"

    if kind == "media":
        label = message.get("text") or ""
        mime = message.get("media_mime") or mimetypes.guess_type(label)[0] or "application/octet-stream"
        encoded = message.get("media_base64") or ""
        if not encoded:
            raise ValueError(f"Media turn '{label}' is missing base64 payload")
        data = base64.b64decode(encoded)
        trace_part = {
            "role": role,
            "kind": "media",
            "media_mime": mime,
            "text": label or f"[{mime}]",
        }
        return [types.Part.from_bytes(data=data, mime_type=mime)], trace_part

    text_content = message.get("text") or message.get("content") or ""
    trace_part = {
        "role": role,
        "kind": "text",
        "text": text_content,
    }
    return [types.Part.from_text(text=text_content)], trace_part
