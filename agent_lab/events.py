"""JSONL event log for Agent Harness Lab runtime actions."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .paths import EVENTS_PATH


@dataclass(frozen=True)
class EventItem:
    timestamp: str
    event_type: str
    payload: dict[str, Any]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def append_event(
    event_type: str,
    payload: dict[str, Any],
    *,
    events_path: Path = EVENTS_PATH,
) -> EventItem:
    """Append one structured event to a JSONL log."""
    event = EventItem(timestamp=utc_now(), event_type=event_type, payload=payload)
    events_path.parent.mkdir(parents=True, exist_ok=True)
    line = {
        "timestamp": event.timestamp,
        "type": event.event_type,
        **event.payload,
    }
    with events_path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(line, ensure_ascii=False, sort_keys=True) + "\n")
    return event


def load_events(events_path: Path = EVENTS_PATH) -> list[EventItem]:
    """Load events from disk, skipping malformed JSONL rows."""
    if not events_path.exists():
        return []

    events: list[EventItem] = []
    for line in events_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(data, dict):
            continue

        timestamp = str(data.pop("timestamp", ""))
        event_type = str(data.pop("type", "unknown"))
        events.append(EventItem(timestamp=timestamp, event_type=event_type, payload=data))
    return events


def tail_events(limit: int = 10, events_path: Path = EVENTS_PATH) -> list[EventItem]:
    """Return the latest events, preserving chronological order."""
    if limit <= 0:
        return []
    return load_events(events_path)[-limit:]
