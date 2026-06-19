import json

from jarvis_codex.plan_viewer import load_next_steps_selection, next_steps_state_path, save_next_steps_selection


def test_next_steps_selection_round_trip(tmp_path):
    state = tmp_path / "state"
    saved = save_next_steps_selection(
        state,
        ["push-gate-2", "bad id", "../escape", "hardware-runtime-gate"],
        "# Proceed Brief",
    )

    assert saved["selected"] == ["push-gate-2", "hardware-runtime-gate"]
    assert saved["brief"] == "# Proceed Brief"
    assert isinstance(saved["updated_at"], int)
    assert load_next_steps_selection(state) == saved


def test_next_steps_selection_defaults_when_missing_or_invalid(tmp_path):
    state = tmp_path / "state"

    assert load_next_steps_selection(state) == {"selected": [], "brief": "", "updated_at": None}

    path = next_steps_state_path(state)
    path.parent.mkdir(parents=True)
    path.write_text("{not json", encoding="utf-8")

    assert load_next_steps_selection(state) == {"selected": [], "brief": "", "updated_at": None}


def test_next_steps_selection_file_shape(tmp_path):
    state = tmp_path / "state"
    save_next_steps_selection(state, ["voice-notification-hardening"], "brief")

    data = json.loads(next_steps_state_path(state).read_text(encoding="utf-8"))
    assert data["selected"] == ["voice-notification-hardening"]
    assert data["brief"] == "brief"
