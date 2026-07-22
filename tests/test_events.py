"""SSE event bus overflow behaviour."""

from __future__ import annotations

from src.eval_workbench.services import events


def test_overflow_keeps_newest_event():
    subscriber = events.subscribe()
    try:
        capacity = subscriber.maxsize
        for i in range(capacity):
            events.publish("progress", {"i": i})
        events.publish("campaign_finished", {"ok": True})

        drained: list[dict] = []
        while not subscriber.empty():
            drained.append(subscriber.get_nowait())

        assert len(drained) == capacity
        assert drained[-1]["type"] == "campaign_finished"
        assert drained[0]["data"]["i"] == 1
    finally:
        events.unsubscribe(subscriber)
