import time

import pytest

from jarvis_codex.pty_supervisor import PtyNotFoundError, PtyPolicyError, PtySupervisor


def _collect_text(supervisor: PtySupervisor, channel_id: str, *, timeout: float = 2.0) -> str:
    deadline = time.time() + timeout
    chunks: list[str] = []
    while time.time() < deadline:
        chunks.extend(chunk.chunk for chunk in supervisor.drain_output(channel_id))
        if chunks:
            return "".join(chunks)
        time.sleep(0.02)
    return "".join(chunks)


def test_spawn_short_lived_command_reads_output():
    supervisor = PtySupervisor()
    result = supervisor.spawn("python3 -c \"print('jarvis')\"", profile="dev-loop")

    try:
        supervisor.get(result.channel_id).wait(timeout=2)
        text = _collect_text(supervisor, result.channel_id)
    finally:
        supervisor.close_all()

    assert "jarvis" in text
    assert result.policy.allowed is True


def test_spawn_blocks_destructive_command_before_process_creation():
    supervisor = PtySupervisor()

    with pytest.raises(PtyPolicyError) as exc:
        supervisor.spawn("git reset --hard HEAD", profile="dev-loop")

    assert exc.value.decision.blocked is True
    assert supervisor.cleanup_finished() == []


def test_spawn_requires_approval_for_observe_profile_non_read_only_command():
    supervisor = PtySupervisor()

    with pytest.raises(PtyPolicyError) as exc:
        supervisor.spawn("python3 -c \"print('jarvis')\"", profile="observe")

    assert exc.value.decision.approval_required is True


def test_spawn_allows_approval_required_command_when_approval_granted():
    supervisor = PtySupervisor()
    result = supervisor.spawn("python3 -c \"print('approved')\"", profile="observe", approval_granted=True)

    try:
        supervisor.get(result.channel_id).wait(timeout=2)
        text = _collect_text(supervisor, result.channel_id)
    finally:
        supervisor.close_all()

    assert "approved" in text
    assert result.policy.approval_required is True
    assert result.approval_granted is True
    assert result.to_dict()["approval_granted"] is True


def test_spawn_still_blocks_hardline_command_when_approval_granted():
    supervisor = PtySupervisor()

    with pytest.raises(PtyPolicyError) as exc:
        supervisor.spawn("git reset --hard HEAD", profile="dev-loop", approval_granted=True)

    assert exc.value.decision.blocked is True


def test_write_input_and_drain_output_from_cat():
    supervisor = PtySupervisor()
    result = supervisor.spawn("cat", profile="observe")

    try:
        supervisor.write(result.channel_id, "hello from pty\n")
        text = _collect_text(supervisor, result.channel_id)
    finally:
        supervisor.close_all()

    assert "hello from pty" in text


def test_next_output_reads_shared_stream_queue():
    supervisor = PtySupervisor()
    result = supervisor.spawn("python3 -c \"print('shared stream')\"", profile="dev-loop")

    try:
        supervisor.get(result.channel_id).wait(timeout=2)
        chunk = supervisor.next_output(timeout=2)
    finally:
        supervisor.close_all()

    assert chunk is not None
    assert chunk.channel_id == result.channel_id
    assert "shared stream" in chunk.chunk


def test_resize_and_kill_running_process():
    supervisor = PtySupervisor()
    result = supervisor.spawn("cat", profile="observe")

    supervisor.resize(result.channel_id, rows=32, cols=100)
    returncode = supervisor.kill(result.channel_id)

    assert isinstance(returncode, int)


def test_resize_rejects_invalid_dimensions():
    supervisor = PtySupervisor()
    result = supervisor.spawn("cat", profile="observe")

    try:
        with pytest.raises(ValueError):
            supervisor.resize(result.channel_id, rows=0, cols=80)
    finally:
        supervisor.close_all()


def test_cleanup_finished_evicts_terminated_channel():
    supervisor = PtySupervisor()
    result = supervisor.spawn("python3 -c \"print('done')\"", profile="dev-loop")

    supervisor.get(result.channel_id).wait(timeout=2)
    removed = supervisor.cleanup_finished()

    assert result.channel_id in removed
    with pytest.raises(PtyNotFoundError):
        supervisor.get(result.channel_id)


def test_close_all_cleans_all_tracked_channels():
    supervisor = PtySupervisor()
    first = supervisor.spawn("cat", profile="observe")
    second = supervisor.spawn("cat", profile="observe")

    supervisor.close_all()

    with pytest.raises(PtyNotFoundError):
        supervisor.get(first.channel_id)
    with pytest.raises(PtyNotFoundError):
        supervisor.get(second.channel_id)


def test_unknown_channel_raises():
    supervisor = PtySupervisor()

    with pytest.raises(PtyNotFoundError):
        supervisor.write("pty_missing", "x")
