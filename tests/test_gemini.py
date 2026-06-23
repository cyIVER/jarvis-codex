from __future__ import annotations

from pathlib import Path

from jarvis_codex.gemini import build_gemini_feasibility, build_gemini_live_evidence_brief, build_gemini_live_validation_plan


def test_gemini_feasibility_without_credentials_is_read_only(tmp_path: Path) -> None:
    feasibility = build_gemini_feasibility({}, tmp_path / "missing-adc.json")

    assert feasibility.status == "NEEDS_CREDENTIALS"
    assert feasibility.auth_modes_present == []
    assert feasibility.network_probe_performed is False
    assert feasibility.service_launch_performed is False
    assert feasibility.oauth_flow_started is False
    assert feasibility.writes_state is False
    assert feasibility.secret_values_exposed is False
    assert "No Gemini credential signal" in feasibility.warnings[0]


def test_gemini_feasibility_detects_api_key_without_exposing_value(tmp_path: Path) -> None:
    feasibility = build_gemini_feasibility({"GEMINI_API_KEY": "secret-value"}, tmp_path / "missing-adc.json")

    assert feasibility.status == "READY_FOR_SERVER_PROTOTYPE"
    assert feasibility.auth_modes_present == ["GEMINI_API_KEY"]
    assert feasibility.gemini_api_key_present is True
    assert feasibility.secret_values_exposed is False
    assert "secret-value" not in str(feasibility.to_dict())
    assert feasibility.browser_direct_requires_ephemeral_tokens is True
    assert any("ephemeral tokens" in warning for warning in feasibility.warnings)


def test_gemini_feasibility_warns_about_google_api_key_precedence(tmp_path: Path) -> None:
    feasibility = build_gemini_feasibility(
        {"GEMINI_API_KEY": "gemini-secret", "GOOGLE_API_KEY": "google-secret"},
        tmp_path / "missing-adc.json",
    )

    assert feasibility.auth_modes_present == ["GEMINI_API_KEY", "GOOGLE_API_KEY"]
    assert any("GOOGLE_API_KEY precedence" in warning for warning in feasibility.warnings)
    assert "gemini-secret" not in str(feasibility.to_dict())
    assert "google-secret" not in str(feasibility.to_dict())


def test_gemini_feasibility_detects_adc_without_starting_oauth(tmp_path: Path) -> None:
    adc_path = tmp_path / "application_default_credentials.json"
    adc_path.write_text("{}", encoding="utf-8")

    feasibility = build_gemini_feasibility({}, adc_path)

    assert feasibility.status == "READY_FOR_SERVER_PROTOTYPE"
    assert feasibility.auth_modes_present == ["application_default_credentials"]
    assert feasibility.application_default_credentials_file_present is True
    assert feasibility.oauth_flow_started is False
    assert any("does not start an OAuth flow" in warning for warning in feasibility.warnings)


def test_gemini_feasibility_keeps_actual_live_connection_as_gate(tmp_path: Path) -> None:
    feasibility = build_gemini_feasibility({"GOOGLE_APPLICATION_CREDENTIALS": "/tmp/creds.json"}, tmp_path / "missing-adc.json")

    assert feasibility.google_application_credentials_present is True
    assert "run an explicit networked Gemini Live connection test only after operator approval" in feasibility.remaining_gates
    assert "https://ai.google.dev/gemini-api/docs/live-api" in feasibility.sources


def test_gemini_validation_plan_without_credentials_is_not_ready(tmp_path: Path) -> None:
    plan = build_gemini_live_validation_plan({}, tmp_path / "missing-adc.json")

    assert plan.status == "NEEDS_CREDENTIALS"
    assert plan.credential_mode_ready is False
    assert plan.network_probe_performed is False
    assert plan.websocket_opened is False
    assert plan.oauth_flow_started is False
    assert plan.service_launch_performed is False
    assert plan.writes_state is False
    assert plan.execution_authority is False
    assert plan.secret_values_exposed is False
    assert any("No credential signal" in warning for warning in plan.warnings)


def test_gemini_validation_plan_with_api_key_does_not_expose_secret(tmp_path: Path) -> None:
    plan = build_gemini_live_validation_plan({"GEMINI_API_KEY": "secret-value"}, tmp_path / "missing-adc.json")

    assert plan.status == "READY_FOR_OPERATOR_TEST"
    assert plan.credential_mode_ready is True
    assert plan.browser_direct_requires_ephemeral_tokens is True
    assert plan.ephemeral_tokens_preview is True
    assert plan.server_to_server_available is True
    assert "secret-value" not in str(plan.to_dict())
    assert any("long-lived API key" in criterion for criterion in plan.fail_criteria)


def test_gemini_validation_plan_names_connection_gates(tmp_path: Path) -> None:
    plan = build_gemini_live_validation_plan({"GOOGLE_API_KEY": "google-secret"}, tmp_path / "missing-adc.json")

    assert any("ephemeral-token" in step for step in plan.validation_steps)
    assert any("WebSocket connection" in step for step in plan.validation_steps)
    assert any("GoAway" in item for item in plan.session_limits_to_verify)
    assert any("do not open Gemini WebSockets" in action for action in plan.unsafe_actions)
    assert "https://ai.google.dev/gemini-api/docs/live-api/ephemeral-tokens" in plan.sources


def test_gemini_evidence_brief_is_read_only_and_release_gate_safe(tmp_path: Path) -> None:
    brief = build_gemini_live_evidence_brief({"GOOGLE_API_KEY": "google-secret"}, tmp_path / "missing-adc.json")

    assert brief.label == "Gemini Live operator evidence brief"
    assert brief.status == "READY_FOR_OPERATOR_TEST"
    assert brief.credential_mode_ready is True
    assert brief.auth_modes_present == ["GOOGLE_API_KEY"]
    assert brief.network_probe_performed is False
    assert brief.oauth_flow_started is False
    assert brief.websocket_opened is False
    assert brief.service_launch_performed is False
    assert brief.writes_state is False
    assert brief.execution_authority is False
    assert brief.secret_values_exposed is False
    assert brief.cloud_spend_authority is False
    assert brief.release_gate_closed is False
    assert brief.requires_human_acceptance is True
    assert "networked_gemini_live_validation" in brief.release_evidence_command
    assert "google-secret" not in str(brief.to_dict())
    assert any("secret values redacted" in step for step in brief.operator_steps)
    assert any("do not close" in action for action in brief.unsafe_actions)


def test_gemini_evidence_brief_without_credentials_is_not_ready(tmp_path: Path) -> None:
    brief = build_gemini_live_evidence_brief({}, tmp_path / "missing-adc.json")

    assert brief.status == "NEEDS_CREDENTIALS"
    assert brief.credential_mode_ready is False
    assert brief.auth_modes_present == []
    assert brief.release_gate_closed is False
    assert "No Gemini credential signal" in brief.warnings[0]
