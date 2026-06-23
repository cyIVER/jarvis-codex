import json

from jarvis_codex.event_store import JarvisEventStore


def test_event_store_appends_events_with_wal(tmp_path):
    store = JarvisEventStore(tmp_path / "runtime" / "jarvis.db")

    event = store.append_event(
        session_id="session-1",
        actor_id="codex",
        source_client="pytest",
        event_type="session.created",
        payload={"title": "Build Jarvis memory"},
        created_at=123,
    )

    assert event.sequence == 1
    assert event.id.startswith("evt_")
    assert store.current_sequence() == 1
    assert store.journal_mode().lower() == "wal"


def test_event_store_creates_core_projection_tables(tmp_path):
    store = JarvisEventStore(tmp_path / "jarvis.db")

    assert {"events", "sessions", "panes", "approvals", "jobs", "event_search"}.issubset(store.table_names())


def test_event_store_updates_session_projection(tmp_path):
    store = JarvisEventStore(tmp_path / "jarvis.db")
    store.append_event(
        session_id="session-1",
        actor_id="user",
        source_client="pytest",
        event_type="session.created",
        payload={"title": "Memory run", "profile_id": "dev-loop", "model_route": {"agent": "codex"}},
        created_at=10,
    )
    store.append_event(
        session_id="session-1",
        actor_id="user",
        source_client="pytest",
        event_type="session.archived",
        payload={},
        created_at=20,
    )

    session = store.session("session-1")

    assert session is not None
    assert session["title"] == "Memory run"
    assert session["profile_id"] == "dev-loop"
    assert session["status"] == "archived"
    assert session["archived_at"] == 20
    assert session["model_route"] == {"agent": "codex"}


def test_event_store_lists_sessions_by_updated_time_and_status(tmp_path):
    store = JarvisEventStore(tmp_path / "jarvis.db")
    store.append_event(
        session_id="session-old",
        actor_id="user",
        source_client="pytest",
        event_type="session.created",
        payload={"title": "Old", "profile_id": "observe", "model_route": {"agent": "codex"}},
        created_at=10,
    )
    store.append_event(
        session_id="session-new",
        actor_id="user",
        source_client="pytest",
        event_type="session.created",
        payload={"title": "New", "profile_id": "dev-loop", "model_route": {"agent": "ag"}},
        created_at=20,
    )
    store.append_event(
        session_id="session-old",
        actor_id="user",
        source_client="pytest",
        event_type="session.archived",
        payload={},
        created_at=30,
    )

    active = store.sessions(status="active")
    archived = store.sessions(status="archived")
    all_sessions = store.sessions(limit=10)

    assert [session["id"] for session in active] == ["session-new"]
    assert [session["id"] for session in archived] == ["session-old"]
    assert [session["id"] for session in all_sessions] == ["session-old", "session-new"]
    assert active[0]["model_route"] == {"agent": "ag"}


def test_event_store_replays_events_in_order(tmp_path):
    store = JarvisEventStore(tmp_path / "jarvis.db")
    first = store.append_event(
        session_id="session-1",
        actor_id="user",
        source_client="pytest",
        event_type="prompt.sent",
        payload={"text": "first"},
        created_at=1,
    )
    second = store.append_event(
        session_id="session-1",
        actor_id="codex",
        source_client="pytest",
        event_type="message.sent",
        payload={"text": "second"},
        parent_event_id=first.id,
        created_at=2,
    )

    events = store.events(session_id="session-1")

    assert [event.id for event in events] == [first.id, second.id]
    assert events[1].parent_event_id == first.id


def test_event_store_searches_payload_projection(tmp_path):
    store = JarvisEventStore(tmp_path / "jarvis.db")
    store.append_event(
        session_id="session-1",
        actor_id="ag",
        source_client="pytest",
        event_type="review.finding",
        payload={"finding": "Gemini OAuth feasibility must be tested"},
    )
    store.append_event(
        session_id="session-2",
        actor_id="codex",
        source_client="pytest",
        event_type="review.finding",
        payload={"finding": "Electron renderer cannot execute shell commands"},
    )

    results = store.search("OAuth")

    assert len(results) == 1
    assert results[0]["session_id"] == "session-1"
    assert results[0]["payload"]["finding"].startswith("Gemini")


def test_event_store_search_treats_query_as_plain_text(tmp_path):
    store = JarvisEventStore(tmp_path / "jarvis.db")
    store.append_event(
        session_id="session-1",
        actor_id="codex",
        source_client="pytest",
        event_type="message.sent",
        payload={"text": "Starlink-8 OAuth check"},
    )

    assert store.search('"Starlink-8" OR OAuth')[0]["session_id"] == "session-1"
    assert store.search("===") == []


def test_event_store_can_rebuild_search_projection(tmp_path):
    store = JarvisEventStore(tmp_path / "jarvis.db")
    store.append_event(
        session_id="session-1",
        actor_id="codex",
        source_client="pytest",
        event_type="memory.note",
        payload={"note": "persistent memory should survive handoff"},
    )

    assert store.rebuild_search_projection() == 1
    assert store.search("handoff")[0]["event_type"] == "memory.note"


def test_event_store_exports_jsonl(tmp_path):
    store = JarvisEventStore(tmp_path / "jarvis.db")
    store.append_event(
        session_id="session-1",
        actor_id="user",
        source_client="pytest",
        event_type="voice.transcript_final",
        payload={"text": "continue the Jarvis harness"},
        created_at=42,
    )

    export_path = store.export_jsonl(tmp_path / "exports" / "session.jsonl", session_id="session-1")
    rows = [json.loads(line) for line in export_path.read_text(encoding="utf-8").splitlines()]

    assert rows[0]["event_type"] == "voice.transcript_final"
    assert rows[0]["payload"] == {"text": "continue the Jarvis harness"}
    assert rows[0]["sequence"] == 1


def test_event_store_iterates_events_without_requiring_session_filter(tmp_path):
    store = JarvisEventStore(tmp_path / "jarvis.db")
    store.append_event(
        session_id="session-1",
        actor_id="user",
        source_client="pytest",
        event_type="prompt.sent",
        payload={"text": "one"},
    )
    store.append_event(
        session_id="session-2",
        actor_id="user",
        source_client="pytest",
        event_type="prompt.sent",
        payload={"text": "two"},
    )

    assert [event.session_id for event in store.iter_events()] == ["session-1", "session-2"]


def test_event_store_projects_approval_lifecycle(tmp_path):
    store = JarvisEventStore(tmp_path / "jarvis.db")
    store.append_event(
        session_id="session-1",
        actor_id="runtime",
        source_client="pytest",
        event_type="approval.requested",
        payload={
            "approval_id": "appr-1",
            "summary": "Run tests",
            "operation": "uv run pytest",
            "risk": "medium",
            "scope": {"command": "uv run pytest tests/test_event_store.py"},
        },
        created_at=10,
    )
    store.append_event(
        session_id="session-1",
        actor_id="user",
        source_client="pytest",
        event_type="approval.responded",
        payload={"approval_id": "appr-1", "status": "approved", "reason": "targeted"},
        created_at=20,
    )

    approval = store.approval("appr-1")

    assert approval is not None
    assert approval["status"] == "approved"
    assert approval["decided_at"] == 20
    assert approval["scope"]["command"].startswith("uv run pytest")
    assert store.approvals(status="approved")[0]["id"] == "appr-1"
