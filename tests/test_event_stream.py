from jarvis_codex.event_store import JarvisEventStore
from jarvis_codex.event_stream import RuntimeEventBroadcaster


def test_runtime_event_broadcaster_fans_out_to_subscribers(tmp_path):
    store = JarvisEventStore(tmp_path / "jarvis.db")
    broadcaster = RuntimeEventBroadcaster()
    first = broadcaster.subscribe()
    second = broadcaster.subscribe()
    event = store.append_event(
        session_id="session-1",
        actor_id="runtime",
        source_client="pytest",
        event_type="approval.requested",
        payload={"approval_id": "appr-1"},
    )

    broadcaster.publish(event)

    assert first.get_nowait().id == event.id
    assert second.get_nowait().id == event.id
    assert broadcaster.subscriber_count() == 2
    broadcaster.unsubscribe(first)
    assert broadcaster.subscriber_count() == 1


def test_runtime_event_broadcaster_drops_oldest_when_subscriber_is_full(tmp_path):
    store = JarvisEventStore(tmp_path / "jarvis.db")
    broadcaster = RuntimeEventBroadcaster(subscriber_queue_size=1)
    subscriber = broadcaster.subscribe()
    old = store.append_event(
        session_id="session-1",
        actor_id="runtime",
        source_client="pytest",
        event_type="old",
        payload={},
    )
    new = store.append_event(
        session_id="session-1",
        actor_id="runtime",
        source_client="pytest",
        event_type="new",
        payload={},
    )

    broadcaster.publish(old)
    broadcaster.publish(new)

    assert subscriber.get_nowait().id == new.id
