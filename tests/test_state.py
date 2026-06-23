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


def test_release_evidence_records_metadata_without_closing_gate(tmp_path):
    state = JarvisState(tmp_path / "state")
    artifact_dir = state.release
    artifact_dir.mkdir(parents=True)
    artifact = artifact_dir / "iphone-validation-note.txt"
    artifact.write_text("iPhone reached private HUD URL", encoding="utf-8")

    evidence = state.record_release_evidence(
        "actual_mobile_device_validation",
        "Operator captured iPhone Safari screenshot.",
        "operator",
        artifact,
    )

    records = state.release_evidence()
    assert evidence.id.startswith("evidence_")
    assert evidence.gate == "actual_mobile_device_validation"
    assert evidence.artifact_path == str(artifact)
    assert evidence.artifact_size_bytes == artifact.stat().st_size
    assert evidence.artifact_sha256
    assert evidence.execution_authority is False
    assert evidence.release_gate_closed is False
    assert records[-1]["release_gate_closed"] is False


def test_release_evidence_rejects_invalid_gate(tmp_path):
    state = JarvisState(tmp_path / "state")

    try:
        state.record_release_evidence("not_a_gate", "Invalid gate")
    except ValueError as exc:
        assert "gate must be one of" in str(exc)
    else:
        raise AssertionError("invalid gate was accepted")


def test_release_evidence_rejects_artifacts_outside_state_release_dir(tmp_path):
    state = JarvisState(tmp_path / "state")
    artifact = tmp_path / "external-note.txt"
    artifact.write_text("do not hash from arbitrary paths", encoding="utf-8")

    try:
        state.record_release_evidence("external_security_review", "External artifact", artifact=artifact)
    except ValueError as exc:
        assert "selected state release directory" in str(exc)
    else:
        raise AssertionError("external artifact path was accepted")


def test_release_evidence_ignores_malformed_jsonl_in_doctor_and_list(tmp_path):
    state = JarvisState(tmp_path / "state")
    state.init()
    (state.release / "evidence.jsonl").write_text('{"gate": "actual_mobile_device_validation"}\nnot-json\n[]\n', encoding="utf-8")

    assert state.release_evidence() == [{"gate": "actual_mobile_device_validation"}]
    assert state.doctor()["release_evidence"] == 1
