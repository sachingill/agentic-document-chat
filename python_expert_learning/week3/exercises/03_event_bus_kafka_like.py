"""
Week 3 - Exercise 3: Kafka-like event bus (local fallback)

We model the Kafka mental model without requiring a Kafka broker:
- Producer publishes events to a topic
- Consumer group reads from the topic
- Offset tracking lives in the consumer

Optional: you can later swap the LocalEventBus with kafka-python or confluent-kafka.

Run:
  python python_expert_learning/week3/exercises/03_event_bus_kafka_like.py
"""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional


@dataclass(frozen=True)
class Event:
    event_id: str
    topic: str
    key: str
    payload: dict
    ts: float


class LocalEventBus:
    """
    A tiny in-memory append-only log per topic.
    This mimics "topic partitions" only at a conceptual level (single partition).
    """

    def __init__(self) -> None:
        self._topics: Dict[str, List[Event]] = {}

    def publish(self, topic: str, key: str, payload: dict) -> Event:
        ev = Event(
            event_id=str(uuid.uuid4()),
            topic=topic,
            key=key,
            payload=payload,
            ts=time.time(),
        )
        self._topics.setdefault(topic, []).append(ev)
        return ev

    def read_from(self, topic: str, offset: int, max_batch: int = 10) -> tuple[list[Event], int]:
        log = self._topics.get(topic, [])
        batch = log[offset : offset + max_batch]
        new_offset = offset + len(batch)
        return batch, new_offset


class Consumer:
    """
    Simple consumer with offset tracking and idempotency hook.
    """

    def __init__(self, bus: LocalEventBus, *, topic: str) -> None:
        self.bus = bus
        self.topic = topic
        self.offset = 0
        self.processed_ids: set[str] = set()  # TODO: replace with DB/Redis for persistence

    def poll(self, handler: Callable[[Event], None], *, max_batch: int = 10) -> int:
        events, new_offset = self.bus.read_from(self.topic, self.offset, max_batch=max_batch)
        for ev in events:
            # Idempotency check (critical for at-least-once processing)
            if ev.event_id in self.processed_ids:
                continue
            handler(ev)
            self.processed_ids.add(ev.event_id)
        self.offset = new_offset
        return len(events)


def main() -> None:
    bus = LocalEventBus()
    topic = "pageviews"

    # Produce events
    for i in range(5):
        bus.publish(topic, key="user-1", payload={"path": f"/p/{i}", "user_id": "user-1"})

    def handler(ev: Event) -> None:
        print("handled:", ev.event_id, ev.payload)

    consumer = Consumer(bus, topic=topic)
    n = consumer.poll(handler, max_batch=100)
    print("polled:", n, "events; offset now:", consumer.offset)

    print("\n✅ Next steps (do these TODOs):")
    print("- Persist processed_ids (simulate with sqlite3) to survive restarts")
    print("- Add a 'dead letter' list when handler throws")
    print("- Add retry policy with backoff (but keep idempotency!)")
    print("- Add a second consumer to model consumer group partitioning (advanced)")


if __name__ == "__main__":
    main()


