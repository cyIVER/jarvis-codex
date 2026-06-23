from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping


GEMINI_LIVE_SOURCES = [
    "https://ai.google.dev/gemini-api/docs/live-api",
    "https://ai.google.dev/gemini-api/docs/live-api/get-started-websocket",
    "https://ai.google.dev/gemini-api/docs/live-api/ephemeral-tokens",
    "https://ai.google.dev/gemini-api/docs/live-api/capabilities",
    "https://ai.google.dev/gemini-api/docs/live-api/best-practices",
    "https://ai.google.dev/gemini-api/docs/oauth",
    "https://ai.google.dev/gemini-api/docs/api-key",
]


@dataclass(frozen=True)
class GeminiFeasibility:
    label: str
    status: str
    auth_modes_present: list[str]
    recommended_path: str
    live_api_protocol: str
    live_api_preview: bool
    server_mediated_recommended: bool
    browser_direct_requires_ephemeral_tokens: bool
    oauth_flow_started: bool
    network_probe_performed: bool
    service_launch_performed: bool
    writes_state: bool
    secret_values_exposed: bool
    gemini_api_key_present: bool
    google_api_key_present: bool
    google_application_credentials_present: bool
    application_default_credentials_file_present: bool
    warnings: list[str]
    remaining_gates: list[str]
    sources: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class GeminiLiveValidationPlan:
    label: str
    status: str
    recommended_path: str
    credential_mode_ready: bool
    browser_direct_requires_ephemeral_tokens: bool
    ephemeral_tokens_preview: bool
    server_to_server_available: bool
    websocket_endpoint_family: str
    session_limits_to_verify: list[str]
    network_probe_performed: bool
    oauth_flow_started: bool
    websocket_opened: bool
    service_launch_performed: bool
    writes_state: bool
    execution_authority: bool
    secret_values_exposed: bool
    required_operator_evidence: list[str]
    validation_steps: list[str]
    pass_criteria: list[str]
    fail_criteria: list[str]
    unsafe_actions: list[str]
    warnings: list[str]
    sources: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class GeminiLiveEvidenceBrief:
    label: str
    status: str
    recommended_path: str
    credential_mode_ready: bool
    auth_modes_present: list[str]
    browser_direct_requires_ephemeral_tokens: bool
    feasibility_command: str
    validation_plan_command: str
    network_test_command: str
    release_evidence_command: str
    required_operator_evidence: list[str]
    operator_steps: list[str]
    pass_criteria: list[str]
    fail_criteria: list[str]
    unsafe_actions: list[str]
    warnings: list[str]
    sources: list[str]
    network_probe_performed: bool
    oauth_flow_started: bool
    websocket_opened: bool
    service_launch_performed: bool
    writes_state: bool
    execution_authority: bool
    secret_values_exposed: bool
    cloud_spend_authority: bool
    release_gate_closed: bool
    requires_human_acceptance: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_gemini_feasibility(
    env: Mapping[str, str] | None = None,
    application_default_credentials_path: Path | None = None,
) -> GeminiFeasibility:
    """Inspect local Gemini Live feasibility without authenticating or connecting."""
    source_env = os.environ if env is None else env
    adc_path = application_default_credentials_path or Path.home() / ".config/gcloud/application_default_credentials.json"

    gemini_api_key_present = bool(source_env.get("GEMINI_API_KEY"))
    google_api_key_present = bool(source_env.get("GOOGLE_API_KEY"))
    google_application_credentials_present = bool(source_env.get("GOOGLE_APPLICATION_CREDENTIALS"))
    adc_file_present = adc_path.exists()

    auth_modes: list[str] = []
    if gemini_api_key_present:
        auth_modes.append("GEMINI_API_KEY")
    if google_api_key_present:
        auth_modes.append("GOOGLE_API_KEY")
    if google_application_credentials_present:
        auth_modes.append("GOOGLE_APPLICATION_CREDENTIALS")
    if adc_file_present:
        auth_modes.append("application_default_credentials")

    warnings: list[str] = []
    if not auth_modes:
        warnings.append("No Gemini credential signal was found; live voice remains unconfigured.")
    if google_api_key_present and gemini_api_key_present:
        warnings.append("Both GOOGLE_API_KEY and GEMINI_API_KEY are present; Google Gen AI SDK documentation gives GOOGLE_API_KEY precedence.")
    if gemini_api_key_present or google_api_key_present:
        warnings.append("Do not expose API keys to the browser; client-to-server Live API should use ephemeral tokens.")
    if google_application_credentials_present or adc_file_present:
        warnings.append("OAuth or ADC may support a server-mediated prototype, but this check does not start an OAuth flow or verify scopes.")

    status = "READY_FOR_SERVER_PROTOTYPE" if auth_modes else "NEEDS_CREDENTIALS"

    return GeminiFeasibility(
        label="Gemini Live feasibility",
        status=status,
        auth_modes_present=auth_modes,
        recommended_path="server-mediated runtime adapter first; browser direct Live API only after ephemeral-token backend design",
        live_api_protocol="stateful WebSocket",
        live_api_preview=True,
        server_mediated_recommended=True,
        browser_direct_requires_ephemeral_tokens=True,
        oauth_flow_started=False,
        network_probe_performed=False,
        service_launch_performed=False,
        writes_state=False,
        secret_values_exposed=False,
        gemini_api_key_present=gemini_api_key_present,
        google_api_key_present=google_api_key_present,
        google_application_credentials_present=google_application_credentials_present,
        application_default_credentials_file_present=adc_file_present,
        warnings=warnings,
        remaining_gates=[
            "choose auth mode: auth API key for server prototype or OAuth/ADC for stricter access controls",
            "design ephemeral-token minting before direct browser Live API access",
            "implement approval-gated Gemini Live adapter without exposing secrets to HUD or PWA clients",
            "run an explicit networked Gemini Live connection test only after operator approval",
            "confirm billing, quotas, key restrictions, and cloud indicator UX before production use",
        ],
        sources=GEMINI_LIVE_SOURCES,
    )


def build_gemini_live_validation_plan(
    env: Mapping[str, str] | None = None,
    application_default_credentials_path: Path | None = None,
) -> GeminiLiveValidationPlan:
    """Prepare a Gemini Live connection validation plan without authenticating, connecting, or writing state."""
    feasibility = build_gemini_feasibility(env, application_default_credentials_path)
    credential_ready = bool(feasibility.auth_modes_present)
    warnings = list(feasibility.warnings)
    if not credential_ready:
        warnings.append("No credential signal is present; do not attempt a networked Gemini Live test yet.")

    return GeminiLiveValidationPlan(
        label="Gemini Live validation plan",
        status="READY_FOR_OPERATOR_TEST" if credential_ready else "NEEDS_CREDENTIALS",
        recommended_path=feasibility.recommended_path,
        credential_mode_ready=credential_ready,
        browser_direct_requires_ephemeral_tokens=True,
        ephemeral_tokens_preview=True,
        server_to_server_available=True,
        websocket_endpoint_family="server-to-server v1beta with API key, or client-to-server v1alpha with ephemeral access_token",
        session_limits_to_verify=[
            "audio-only sessions have documented duration limits",
            "audio plus video sessions have shorter documented duration limits",
            "session resumption and GoAway handling are required for robust long-running UX",
        ],
        network_probe_performed=False,
        oauth_flow_started=False,
        websocket_opened=False,
        service_launch_performed=False,
        writes_state=False,
        execution_authority=False,
        secret_values_exposed=False,
        required_operator_evidence=[
            "approved credential mode and key restriction or OAuth/ADC note",
            "billing and quota confirmation",
            "chosen model and endpoint family",
            "confirmation that browser clients receive only ephemeral tokens if browser-direct is used",
            "captured setup/response metadata with secret values redacted",
            "cloud indicator UX screenshot or note",
        ],
        validation_steps=[
            "Run gemini feasibility first and confirm a credential signal is present.",
            "Choose server-mediated runtime adapter before browser-direct Live API.",
            "If browser-direct is required, design and review ephemeral-token minting first.",
            "Approve the exact networked WebSocket connection test command before opening any WebSocket.",
            "Send only a minimal setup message and low-risk text/audio sample during the first test.",
            "Verify session duration, GoAway, generationComplete, and resumption behavior before production use.",
            "Record only redacted metadata and do not store raw secrets or sensitive audio by default.",
        ],
        pass_criteria=[
            "no long-lived API key is exposed to HUD, PWA, logs, or browser code",
            "networked test is explicitly approved before WebSocket connection",
            "cloud voice path is visibly labeled in HUD/PWA",
            "Live API tool calls remain routed through existing local policy and approval boundaries",
            "local STT/TTS fallback remains available",
        ],
        fail_criteria=[
            "browser receives a long-lived API key",
            "OAuth flow or WebSocket connection starts without explicit approval",
            "secret values appear in stdout, logs, state, docs, or screenshots",
            "Live API tool calls bypass local approvals or PTY policy",
            "cloud path replaces local fallback without an operator decision",
        ],
        unsafe_actions=[
            "do not start OAuth from this validation-plan command",
            "do not open Gemini WebSockets from this validation-plan command",
            "do not launch services or runtime adapters from this validation-plan command",
            "do not store or print API keys, access tokens, OAuth refresh tokens, or ADC JSON",
            "do not treat feasibility or validation-plan output as approval for cloud spend or network calls",
        ],
        warnings=warnings,
        sources=GEMINI_LIVE_SOURCES,
    )


def build_gemini_live_evidence_brief(
    env: Mapping[str, str] | None = None,
    application_default_credentials_path: Path | None = None,
) -> GeminiLiveEvidenceBrief:
    """Prepare a compact Gemini Live operator evidence brief without network, auth, or state side effects."""
    feasibility = build_gemini_feasibility(env, application_default_credentials_path)
    plan = build_gemini_live_validation_plan(env, application_default_credentials_path)
    release_summary = (
        "Networked Gemini Live validation with redacted credential mode, WebSocket result metadata, "
        "cloud indicator evidence, and local fallback boundary confirmation."
    )
    release_command = (
        "jarvis-codex --state <state-dir> release evidence add "
        "--gate networked_gemini_live_validation "
        f"--summary {json.dumps(release_summary)} --reviewer operator --json"
    )
    warnings = list(dict.fromkeys([*feasibility.warnings, *plan.warnings]))
    return GeminiLiveEvidenceBrief(
        label="Gemini Live operator evidence brief",
        status=plan.status,
        recommended_path=plan.recommended_path,
        credential_mode_ready=plan.credential_mode_ready,
        auth_modes_present=feasibility.auth_modes_present,
        browser_direct_requires_ephemeral_tokens=plan.browser_direct_requires_ephemeral_tokens,
        feasibility_command="jarvis-codex gemini feasibility --json",
        validation_plan_command="jarvis-codex gemini validation-plan --json",
        network_test_command="future approved Gemini Live adapter command; not implemented or executed by this brief",
        release_evidence_command=release_command,
        required_operator_evidence=[
            *plan.required_operator_evidence,
            "approved exact network test command and captured exit/status result",
            "confirmation that no long-lived credential was exposed to HUD, PWA, logs, or browser code",
            "confirmation that local STT/TTS fallback remained available after the cloud test",
        ],
        operator_steps=[
            "Run the feasibility and validation-plan commands first.",
            "Confirm the credential mode, billing/quota posture, and endpoint family before any networked test.",
            "Review and approve the exact Gemini Live adapter command before OAuth, WebSocket, or network activity.",
            "Run only a minimal redacted network test after approval.",
            "Capture setup/result metadata with secret values redacted.",
            "Store any evidence artifact under <state-dir>/release/ before hashing it with release evidence add.",
            "Record release evidence metadata only after a human reviews the redacted evidence.",
        ],
        pass_criteria=plan.pass_criteria,
        fail_criteria=plan.fail_criteria,
        unsafe_actions=[
            *plan.unsafe_actions,
            "do not treat this brief as proof that Gemini Live connected",
            "do not treat this brief as approval for cloud spend",
            "do not run a future adapter command without exact operator approval",
            "do not close the networked_gemini_live_validation gate from this brief",
        ],
        warnings=warnings,
        sources=plan.sources,
        network_probe_performed=False,
        oauth_flow_started=False,
        websocket_opened=False,
        service_launch_performed=False,
        writes_state=False,
        execution_authority=False,
        secret_values_exposed=False,
        cloud_spend_authority=False,
        release_gate_closed=False,
        requires_human_acceptance=True,
    )
