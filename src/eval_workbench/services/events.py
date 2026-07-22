"""In-process pub/sub for SSE job and domain events."""

from __future__ import annotations

import queue
import threading
from typing import Any

_subscribers: list[queue.Queue[dict[str, Any]]] = []
_lock = threading.Lock()

# Prefer keeping recent events (including completion) over blocking publishers.
_QUEUE_SIZE = 512


def publish(event_type: str, data: dict[str, Any]) -> None:
    message = {"type": event_type, "data": data}
    with _lock:
        for subscriber in list(_subscribers):
            _enqueue(subscriber, message)


def _enqueue(subscriber: queue.Queue[dict[str, Any]], message: dict[str, Any]) -> None:
    """Push an event; if the queue is full, drop the oldest and retry once."""
    try:
        subscriber.put_nowait(message)
        return
    except queue.Full:
        pass
    try:
        subscriber.get_nowait()
    except queue.Empty:
        pass
    try:
        subscriber.put_nowait(message)
    except queue.Full:
        pass


def subscribe() -> queue.Queue[dict[str, Any]]:
    subscriber: queue.Queue[dict[str, Any]] = queue.Queue(maxsize=_QUEUE_SIZE)
    with _lock:
        _subscribers.append(subscriber)
    return subscriber


def unsubscribe(subscriber: queue.Queue[dict[str, Any]]) -> None:
    with _lock:
        if subscriber in _subscribers:
            _subscribers.remove(subscriber)


def publish_cases_modified(action: str, case_id: str | None = None) -> None:
    payload: dict[str, Any] = {"action": action}
    if case_id:
        payload["case_id"] = case_id
    publish("cases_modified", payload)
