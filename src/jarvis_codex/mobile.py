from __future__ import annotations

import ipaddress
from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class MobilePreflight:
    host: str
    port: int
    scheme: str
    url: str
    host_class: str
    iphone_reachable_candidate: bool
    requires_allow_non_loopback: bool
    public_exposure_risk: bool
    runtime_command: str
    writes_state: bool
    network_probe_performed: bool
    service_launch_performed: bool
    checklist: list[str]
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_mobile_preflight(host: str = "127.0.0.1", port: int = 8765, scheme: str = "http") -> MobilePreflight:
    normalized_host = host.strip() or "127.0.0.1"
    normalized_scheme = scheme.strip().lower() or "http"
    if normalized_scheme not in {"http", "https"}:
        raise ValueError("scheme must be http or https")
    if port < 1 or port > 65535:
        raise ValueError("port must be between 1 and 65535")

    host_class = classify_mobile_host(normalized_host)
    requires_allow = host_class != "loopback"
    public_risk = host_class in {"bind-all", "public", "unknown-hostname"}
    iphone_candidate = host_class in {"private-lan", "tailscale-cgnat", "vpn-or-link-local", "bind-all"}
    display_host = normalized_host if ":" not in normalized_host else f"[{normalized_host}]"
    command = f"jarvis-codex runtime serve --host {normalized_host} --port {port}"
    if requires_allow:
        command += " --allow-non-loopback"

    warnings: list[str] = []
    if host_class == "loopback":
        warnings.append("Loopback is safe for desktop but is not reachable from an iPhone.")
    if host_class == "bind-all":
        warnings.append("0.0.0.0 binds every interface; confirm firewall and private VPN boundaries before use.")
    if public_risk and host_class != "bind-all":
        warnings.append("Host does not classify as private; do not use for v1 mobile access without a separate security review.")

    return MobilePreflight(
        host=normalized_host,
        port=port,
        scheme=normalized_scheme,
        url=f"{normalized_scheme}://{display_host}:{port}",
        host_class=host_class,
        iphone_reachable_candidate=iphone_candidate,
        requires_allow_non_loopback=requires_allow,
        public_exposure_risk=public_risk,
        runtime_command=command,
        writes_state=False,
        network_probe_performed=False,
        service_launch_performed=False,
        checklist=[
            "Run the runtime only after choosing a private LAN, Tailscale, or WireGuard address.",
            "Keep public tunnels disabled for v1.",
            "Confirm iPhone Safari can reach the URL over the private network.",
            "Confirm microphone permission requires a user click.",
            "Confirm approvals show operation, risk, and scope before approve or reject.",
            "Confirm the service worker does not cache /rpc, /ws, or non-GET requests.",
        ],
        warnings=warnings,
    )


def classify_mobile_host(host: str) -> str:
    lowered = host.strip().lower()
    if lowered in {"localhost", "127.0.0.1", "::1", "[::1]"}:
        return "loopback"
    if lowered in {"0.0.0.0", "::"}:
        return "bind-all"
    try:
        address = ipaddress.ip_address(lowered.strip("[]"))
    except ValueError:
        return "unknown-hostname"
    if address.is_loopback:
        return "loopback"
    if address.version == 4 and ipaddress.ip_address("100.64.0.0") <= address <= ipaddress.ip_address("100.127.255.255"):
        return "tailscale-cgnat"
    if address.is_private:
        return "private-lan"
    if address.is_link_local:
        return "vpn-or-link-local"
    return "public"
