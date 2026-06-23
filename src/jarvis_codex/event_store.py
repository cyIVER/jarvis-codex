from __future__ import annotations

import json
import re
import sqlite3
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from collections.abc import Iterator
from typing import Any


SCHEMA_VERSION = 1


@dataclass(frozen=True)
class StoredEvent:
    sequence: int
    id: str
    session_id: str
    actor_id: str
    source_client: str
    event_type: str
    payload: dict[str, Any]
    correlation_id: str | None
    parent_event_id: str | None
    created_at: int


class JarvisEventStore:
    """SQLite/WAL append-only event store for Jarvis runtime state."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self._initialized = False

    def initialize(self) -> None:
        if self._initialized:
            return
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connection() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS meta (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS events (
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                    id TEXT NOT NULL UNIQUE,
                    session_id TEXT NOT NULL,
                    actor_id TEXT NOT NULL,
                    source_client TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    correlation_id TEXT,
                    parent_event_id TEXT,
                    created_at INTEGER NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_events_session_sequence
                    ON events(session_id, sequence);

                CREATE INDEX IF NOT EXISTS idx_events_type_sequence
                    ON events(event_type, sequence);

                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    profile_id TEXT NOT NULL,
                    source_client TEXT NOT NULL,
                    parent_session_id TEXT,
                    model_route TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at INTEGER NOT NULL,
                    updated_at INTEGER NOT NULL,
                    archived_at INTEGER
                );

                CREATE TABLE IF NOT EXISTS panes (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    command_label TEXT NOT NULL,
                    cwd TEXT NOT NULL,
                    policy_profile TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at INTEGER NOT NULL,
                    ended_at INTEGER
                );

                CREATE TABLE IF NOT EXISTS approvals (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    operation TEXT NOT NULL,
                    risk TEXT NOT NULL,
                    status TEXT NOT NULL,
                    scope_json TEXT NOT NULL,
                    created_at INTEGER NOT NULL,
                    decided_at INTEGER
                );

                CREATE TABLE IF NOT EXISTS jobs (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    status TEXT NOT NULL,
                    owner_role TEXT NOT NULL,
                    started_at INTEGER NOT NULL,
                    ended_at INTEGER,
                    last_event_sequence INTEGER NOT NULL
                );
                """
            )
            connection.execute(
                """
                CREATE VIRTUAL TABLE IF NOT EXISTS event_search
                USING fts5(event_id UNINDEXED, session_id UNINDEXED, event_type, content)
                """
            )
            connection.execute(
                """
                INSERT INTO meta(key, value)
                VALUES('schema_version', ?)
                ON CONFLICT(key) DO UPDATE SET value=excluded.value
                """,
                (str(SCHEMA_VERSION),),
            )
        self._initialized = True

    def append_event(
        self,
        *,
        session_id: str,
        actor_id: str,
        source_client: str,
        event_type: str,
        payload: dict[str, Any],
        correlation_id: str | None = None,
        parent_event_id: str | None = None,
        created_at: int | None = None,
    ) -> StoredEvent:
        self.initialize()
        event_id = f"evt_{uuid.uuid4().hex[:16]}"
        timestamp = int(time.time()) if created_at is None else created_at
        payload_json = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        with self._connection() as connection:
            cursor = connection.execute(
                """
                INSERT INTO events(
                    id,
                    session_id,
                    actor_id,
                    source_client,
                    event_type,
                    payload_json,
                    correlation_id,
                    parent_event_id,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event_id,
                    session_id,
                    actor_id,
                    source_client,
                    event_type,
                    payload_json,
                    correlation_id,
                    parent_event_id,
                    timestamp,
                ),
            )
            sequence = int(cursor.lastrowid)
            connection.execute(
                """
                INSERT INTO event_search(event_id, session_id, event_type, content)
                VALUES (?, ?, ?, ?)
                """,
                (event_id, session_id, event_type, _search_content(payload)),
            )
            self._update_projections(
                connection,
                sequence=sequence,
                session_id=session_id,
                source_client=source_client,
                event_type=event_type,
                payload=payload,
                created_at=timestamp,
            )
        return StoredEvent(
            sequence=sequence,
            id=event_id,
            session_id=session_id,
            actor_id=actor_id,
            source_client=source_client,
            event_type=event_type,
            payload=payload,
            correlation_id=correlation_id,
            parent_event_id=parent_event_id,
            created_at=timestamp,
        )

    def events(self, session_id: str | None = None) -> list[StoredEvent]:
        self.initialize()
        query = "SELECT * FROM events"
        args: tuple[str, ...] = ()
        if session_id is not None:
            query += " WHERE session_id = ?"
            args = (session_id,)
        query += " ORDER BY sequence ASC"
        with self._connection() as connection:
            rows = connection.execute(query, args).fetchall()
        return [_event_from_row(row) for row in rows]

    def search(self, query: str, limit: int = 20) -> list[dict[str, Any]]:
        self.initialize()
        term = _fts_query(query)
        if not term:
            return []
        with self._connection() as connection:
            rows = connection.execute(
                """
                SELECT
                    e.sequence,
                    e.id,
                    e.session_id,
                    e.event_type,
                    e.payload_json,
                    e.created_at
                FROM event_search s
                JOIN events e ON e.id = s.event_id
                WHERE event_search MATCH ?
                ORDER BY e.sequence DESC
                LIMIT ?
                """,
                (term, limit),
            ).fetchall()
        return [
            {
                "sequence": int(row["sequence"]),
                "id": str(row["id"]),
                "session_id": str(row["session_id"]),
                "event_type": str(row["event_type"]),
                "payload": json.loads(str(row["payload_json"])),
                "created_at": int(row["created_at"]),
            }
            for row in rows
        ]

    def rebuild_search_projection(self) -> int:
        self.initialize()
        count = 0
        with self._connection() as connection:
            connection.execute("DELETE FROM event_search")
            cursor = connection.execute("SELECT id, session_id, event_type, payload_json FROM events")
            while True:
                rows = cursor.fetchmany(500)
                if not rows:
                    break
                count += len(rows)
                connection.executemany(
                    """
                    INSERT INTO event_search(event_id, session_id, event_type, content)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        (
                            str(row["id"]),
                            str(row["session_id"]),
                            str(row["event_type"]),
                            _search_content(json.loads(str(row["payload_json"]))),
                        )
                        for row in rows
                    ),
                )
        return count

    def export_jsonl(self, path: Path, session_id: str | None = None) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as handle:
            for event in self.iter_events(session_id=session_id):
                handle.write(json.dumps(_event_to_json(event), sort_keys=True) + "\n")
        return path

    def iter_events(self, session_id: str | None = None) -> Iterator[StoredEvent]:
        self.initialize()
        query = "SELECT * FROM events"
        args: tuple[str, ...] = ()
        if session_id is not None:
            query += " WHERE session_id = ?"
            args = (session_id,)
        query += " ORDER BY sequence ASC"
        with self._connection() as connection:
            cursor = connection.execute(query, args)
            while True:
                rows = cursor.fetchmany(500)
                if not rows:
                    break
                for row in rows:
                    yield _event_from_row(row)

    def session(self, session_id: str) -> dict[str, Any] | None:
        self.initialize()
        with self._connection() as connection:
            row = connection.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
        return dict(row) if row is not None else None

    def approval(self, approval_id: str) -> dict[str, Any] | None:
        self.initialize()
        with self._connection() as connection:
            row = connection.execute("SELECT * FROM approvals WHERE id = ?", (approval_id,)).fetchone()
        return _approval_from_row(row) if row is not None else None

    def approvals(self, status: str | None = None) -> list[dict[str, Any]]:
        self.initialize()
        query = "SELECT * FROM approvals"
        args: tuple[str, ...] = ()
        if status is not None:
            query += " WHERE status = ?"
            args = (status,)
        query += " ORDER BY created_at ASC, id ASC"
        with self._connection() as connection:
            rows = connection.execute(query, args).fetchall()
        return [_approval_from_row(row) for row in rows]

    def table_names(self) -> set[str]:
        self.initialize()
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT name FROM sqlite_master WHERE type IN ('table', 'virtual table')"
            ).fetchall()
        return {str(row["name"]) for row in rows}

    def current_sequence(self) -> int:
        self.initialize()
        with self._connection() as connection:
            value = connection.execute("SELECT COALESCE(MAX(sequence), 0) FROM events").fetchone()[0]
        return int(value)

    def journal_mode(self) -> str:
        self.initialize()
        with self._connection() as connection:
            value = connection.execute("PRAGMA journal_mode").fetchone()[0]
        return str(value)

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        connection = self._connect()
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA foreign_keys=ON")
        return connection

    def _update_projections(
        self,
        connection: sqlite3.Connection,
        *,
        sequence: int,
        session_id: str,
        source_client: str,
        event_type: str,
        payload: dict[str, Any],
        created_at: int,
    ) -> None:
        if event_type == "session.created":
            title = str(payload.get("title") or "Untitled session")
            profile_id = str(payload.get("profile_id") or "observe")
            parent_session_id = payload.get("parent_session_id")
            model_route = json.dumps(payload.get("model_route") or {}, sort_keys=True)
            connection.execute(
                """
                INSERT INTO sessions(
                    id,
                    title,
                    profile_id,
                    source_client,
                    parent_session_id,
                    model_route,
                    status,
                    created_at,
                    updated_at,
                    archived_at
                )
                VALUES (?, ?, ?, ?, ?, ?, 'active', ?, ?, NULL)
                ON CONFLICT(id) DO UPDATE SET
                    title=excluded.title,
                    profile_id=excluded.profile_id,
                    source_client=excluded.source_client,
                    parent_session_id=excluded.parent_session_id,
                    model_route=excluded.model_route,
                    status='active',
                    updated_at=excluded.updated_at,
                    archived_at=NULL
                """,
                (
                    session_id,
                    title,
                    profile_id,
                    source_client,
                    parent_session_id if isinstance(parent_session_id, str) else None,
                    model_route,
                    created_at,
                    created_at,
                ),
            )
            return

        if event_type == "session.archived":
            connection.execute(
                """
                UPDATE sessions
                SET status = 'archived',
                    updated_at = ?,
                    archived_at = ?
                WHERE id = ?
                """,
                (created_at, created_at, session_id),
            )
            return

        if event_type == "approval.requested":
            approval_id = str(payload["approval_id"])
            scope_json = json.dumps(payload.get("scope") or {}, sort_keys=True)
            connection.execute(
                """
                INSERT INTO approvals(
                    id,
                    session_id,
                    summary,
                    operation,
                    risk,
                    status,
                    scope_json,
                    created_at,
                    decided_at
                )
                VALUES (?, ?, ?, ?, ?, 'pending', ?, ?, NULL)
                ON CONFLICT(id) DO UPDATE SET
                    summary=excluded.summary,
                    operation=excluded.operation,
                    risk=excluded.risk,
                    status='pending',
                    scope_json=excluded.scope_json,
                    decided_at=NULL
                """,
                (
                    approval_id,
                    session_id,
                    str(payload.get("summary") or ""),
                    str(payload.get("operation") or ""),
                    str(payload.get("risk") or "medium"),
                    scope_json,
                    created_at,
                ),
            )
            return

        if event_type == "approval.responded":
            approval_id = str(payload["approval_id"])
            status = str(payload["status"])
            connection.execute(
                """
                UPDATE approvals
                SET status = ?,
                    decided_at = ?
                WHERE id = ?
                """,
                (status, created_at, approval_id),
            )
            return

        connection.execute(
            """
            UPDATE sessions
            SET updated_at = ?
            WHERE id = ?
            """,
            (created_at, session_id),
        )


def _event_from_row(row: sqlite3.Row) -> StoredEvent:
    return StoredEvent(
        sequence=int(row["sequence"]),
        id=str(row["id"]),
        session_id=str(row["session_id"]),
        actor_id=str(row["actor_id"]),
        source_client=str(row["source_client"]),
        event_type=str(row["event_type"]),
        payload=json.loads(str(row["payload_json"])),
        correlation_id=row["correlation_id"],
        parent_event_id=row["parent_event_id"],
        created_at=int(row["created_at"]),
    )


def _event_to_json(event: StoredEvent) -> dict[str, Any]:
    return {
        "sequence": event.sequence,
        "id": event.id,
        "session_id": event.session_id,
        "actor_id": event.actor_id,
        "source_client": event.source_client,
        "event_type": event.event_type,
        "payload": event.payload,
        "correlation_id": event.correlation_id,
        "parent_event_id": event.parent_event_id,
        "created_at": event.created_at,
    }


def _approval_from_row(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": str(row["id"]),
        "session_id": str(row["session_id"]),
        "summary": str(row["summary"]),
        "operation": str(row["operation"]),
        "risk": str(row["risk"]),
        "status": str(row["status"]),
        "scope": json.loads(str(row["scope_json"])),
        "created_at": int(row["created_at"]),
        "decided_at": int(row["decided_at"]) if row["decided_at"] is not None else None,
    }


def _search_content(payload: dict[str, Any]) -> str:
    parts: list[str] = []
    _flatten(payload, parts)
    return " ".join(parts)


def _fts_query(query: str) -> str:
    # Treat user text as plain terms instead of exposing the FTS query language.
    operators = {"and", "or", "not"}
    terms = [term for term in re.findall(r"\w+", query.lower()) if term not in operators]
    return " ".join(terms)


def _flatten(value: Any, parts: list[str]) -> None:
    if isinstance(value, dict):
        for child in value.values():
            _flatten(child, parts)
    elif isinstance(value, (list, tuple)):
        for child in value:
            _flatten(child, parts)
    elif value is not None:
        parts.append(str(value))
