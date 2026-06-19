from jarvis_codex.state import JarvisState


def test_capture_memory_and_handoff(tmp_path):
    state = JarvisState(tmp_path / "state")
    episode = state.capture_episode("Build the voice loop")
    memory = state.add_memory("tone", "pragmatic")
    approval = state.request_approval("Run Codex against a repo")
    handoff = state.write_handoff("Ship the prototype")

    assert episode.id.startswith("ep_")
    assert memory.id.startswith("mem_")
    assert approval.id.startswith("approval_")
    text = handoff.read_text()
    assert "Ship the prototype" in text
    assert "Build the voice loop" in text
    assert "tone: pragmatic" in text

