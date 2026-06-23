from __future__ import annotations

import ipaddress
import json
import subprocess
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


@dataclass(frozen=True)
class MobileValidationPlan:
    label: str
    status: str
    target_url: str
    host_class: str
    iphone_reachable_candidate: bool
    network_probe_performed: bool
    service_launch_performed: bool
    writes_state: bool
    execution_authority: bool
    required_operator_evidence: list[str]
    device_test_steps: list[str]
    pass_criteria: list[str]
    fail_criteria: list[str]
    unsafe_actions: list[str]
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MobileHostCandidate:
    interface: str
    host: str
    host_class: str
    url: str
    iphone_reachable_candidate: bool
    public_exposure_risk: bool
    requires_allow_non_loopback: bool
    runtime_command: str
    preflight_command: str
    validation_plan_command: str
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MobileHostDiscovery:
    label: str
    status: str
    port: int
    scheme: str
    candidates: list[MobileHostCandidate]
    recommended_candidate: MobileHostCandidate | None
    writes_state: bool
    network_probe_performed: bool
    service_launch_performed: bool
    browser_opened: bool
    execution_authority: bool
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["candidates"] = [candidate.to_dict() for candidate in self.candidates]
        data["recommended_candidate"] = self.recommended_candidate.to_dict() if self.recommended_candidate else None
        return data


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


def discover_mobile_hosts(
    port: int = 8765,
    scheme: str = "http",
    interface_records: list[dict[str, Any]] | None = None,
) -> MobileHostDiscovery:
    """Discover local mobile host candidates without serving, probing, opening browsers, or writing state."""
    if scheme not in {"http", "https"}:
        raise ValueError("scheme must be http or https")
    if port < 1 or port > 65535:
        raise ValueError("port must be between 1 and 65535")
    records = interface_records if interface_records is not None else _read_ipv4_interfaces()
    warnings: list[str] = []
    if not records:
        warnings.append("No IPv4 interface records were found; choose a private LAN, Tailscale, or WireGuard address manually.")
    candidates = _mobile_candidates_from_interfaces(records, port=port, scheme=scheme)
    recommended = next((candidate for candidate in candidates if candidate.iphone_reachable_candidate and not candidate.public_exposure_risk), None)
    status = "READY_FOR_OPERATOR_TEST" if recommended else "NEEDS_PRIVATE_INTERFACE"
    return MobileHostDiscovery(
        label="Jarvis mobile host discovery",
        status=status,
        port=port,
        scheme=scheme,
        candidates=candidates,
        recommended_candidate=recommended,
        writes_state=False,
        network_probe_performed=False,
        service_launch_performed=False,
        browser_opened=False,
        execution_authority=False,
        warnings=warnings,
    )


def build_mobile_validation_plan(host: str = "127.0.0.1", port: int = 8765, scheme: str = "http") -> MobileValidationPlan:
    """Prepare a private-network iPhone/PWA validation plan without serving, probing, or writing state."""
    preflight = build_mobile_preflight(host, port, scheme)
    warnings = list(preflight.warnings)
    if not preflight.iphone_reachable_candidate:
        warnings.append("Target URL is not classified as iPhone-reachable; choose a private LAN, Tailscale, or WireGuard address.")
    if preflight.public_exposure_risk:
        warnings.append("Do not validate mobile access on a public host without a separate security review.")

    status = "READY_FOR_OPERATOR_TEST" if preflight.iphone_reachable_candidate and not preflight.public_exposure_risk else "NEEDS_PRIVATE_TARGET"

    return MobileValidationPlan(
        label="Jarvis mobile PWA validation plan",
        status=status,
        target_url=preflight.url,
        host_class=preflight.host_class,
        iphone_reachable_candidate=preflight.iphone_reachable_candidate,
        network_probe_performed=False,
        service_launch_performed=False,
        writes_state=False,
        execution_authority=False,
        required_operator_evidence=[
            "screenshot of iPhone Safari loading the Jarvis HUD URL",
            "confirmation that the PWA install prompt or standalone launch works if tested",
            "confirmation that microphone permission appears only after tapping the microphone control",
            "screenshot or note showing approval cards expose operation, risk, and scope",
            "note that the runtime was served only on an approved private-network address",
        ],
        device_test_steps=[
            "Run mobile preflight first and confirm the target is private-network or VPN scoped.",
            "Start the runtime only after approving the exact serve command and bind address.",
            "Open the target URL from iPhone Safari on the same private network or VPN.",
            "Verify the HUD loads without mixed-content or certificate warnings that hide controls.",
            "Tap the microphone control and confirm microphone permission is user-initiated.",
            "Submit a text prompt and confirm it records a semantic prompt without command execution.",
            "Review a pending approval and confirm approve/reject controls remain explicit and scoped.",
            "Stop the runtime when validation is complete.",
        ],
        pass_criteria=[
            "iPhone reaches the HUD over the approved private-network URL",
            "microphone permission requires a user click",
            "voice/text prompt submission does not execute shell commands",
            "approval cards show operation, risk, and scope before approval",
            "service worker does not cache /rpc, /ws, or non-GET requests",
        ],
        fail_criteria=[
            "runtime is reachable from a public address",
            "microphone permission is requested before user interaction",
            "displayed commands execute from the browser",
            "approval state can be changed without explicit approve/reject action",
            "runtime was served on a non-loopback address without operator approval",
        ],
        unsafe_actions=[
            "do not launch the runtime from this validation-plan command",
            "do not probe the network from this validation-plan command",
            "do not open browser or iPhone URLs from this validation-plan command",
            "do not treat checklist completion as approval for git, Worktrunk, local ML, Docker, service, or daemon commands",
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


def _read_ipv4_interfaces() -> list[dict[str, Any]]:
    try:
        result = subprocess.run(["ip", "-j", "-4", "addr", "show"], capture_output=True, text=True, timeout=5, check=False)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return []
    if result.returncode != 0:
        return []
    try:
        value = json.loads(result.stdout)
    except json.JSONDecodeError:
        return []
    return value if isinstance(value, list) else []


def _mobile_candidates_from_interfaces(records: list[dict[str, Any]], port: int, scheme: str) -> list[MobileHostCandidate]:
    candidates: list[MobileHostCandidate] = []
    for record in records:
        interface = str(record.get("ifname") or "unknown")
        flags = {str(flag) for flag in record.get("flags") or []}
        is_loopback_interface = "LOOPBACK" in flags
        for address in record.get("addr_info") or []:
            if address.get("family") != "inet":
                continue
            host = str(address.get("local") or "")
            if not host:
                continue
            preflight = build_mobile_preflight(host, port, scheme)
            warnings = list(preflight.warnings)
            iphone_candidate = preflight.iphone_reachable_candidate and not is_loopback_interface
            if is_loopback_interface:
                warnings.append("Interface is loopback-scoped; do not treat this address as iPhone-reachable.")
            candidates.append(
                MobileHostCandidate(
                    interface=interface,
                    host=host,
                    host_class=preflight.host_class,
                    url=preflight.url,
                    iphone_reachable_candidate=iphone_candidate,
                    public_exposure_risk=preflight.public_exposure_risk,
                    requires_allow_non_loopback=preflight.requires_allow_non_loopback,
                    runtime_command=preflight.runtime_command,
                    preflight_command=f"jarvis-codex mobile preflight --host {host} --port {port} --scheme {scheme} --json",
                    validation_plan_command=f"jarvis-codex mobile validation-plan --host {host} --port {port} --scheme {scheme} --json",
                    warnings=warnings,
                )
            )
    return candidates
