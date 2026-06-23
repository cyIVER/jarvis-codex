from __future__ import annotations

import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping


GEMINI_LIVE_SOURCES = [
    "https://ai.google.dev/gemini-api/docs/live-api",
    "https://ai.google.dev/gemini-api/docs/live-api/get-started-websocket",
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
