from __future__ import annotations

import queue
import threading

from .event_store import StoredEvent


class RuntimeEventBroadcaster:
    def __init__(self, *, subscriber_queue_size: int = 200) -> None:
        self._subscriber_queue_size = subscriber_queue_size
        self._subscribers: set[queue.Queue[StoredEvent]] = set()
        self._lock = threading.Lock()

    def subscribe(self) -> queue.Queue[StoredEvent]:
        subscriber: queue.Queue[StoredEvent] = queue.Queue(maxsize=self._subscriber_queue_size)
        with self._lock:
            self._subscribers.add(subscriber)
        return subscriber

    def unsubscribe(self, subscriber: queue.Queue[StoredEvent]) -> None:
        with self._lock:
            self._subscribers.discard(subscriber)

    def publish(self, event: StoredEvent) -> None:
        with self._lock:
            subscribers = list(self._subscribers)
        for subscriber in subscribers:
            self._put_latest(subscriber, event)

    def subscriber_count(self) -> int:
        with self._lock:
            return len(self._subscribers)

    def _put_latest(self, subscriber: queue.Queue[StoredEvent], event: StoredEvent) -> None:
        try:
            subscriber.put_nowait(event)
            return
        except queue.Full:
            pass
        try:
            subscriber.get_nowait()
        except queue.Empty:
            pass
        try:
            subscriber.put_nowait(event)
        except queue.Full:
            pass
