from __future__ import annotations

import pytest

from jarvis_codex.mobile import (
    build_mobile_evidence_brief,
    build_mobile_preflight,
    build_mobile_validation_plan,
    classify_mobile_host,
    discover_mobile_hosts,
)


def test_mobile_preflight_keeps_loopback_safe_but_not_iphone_reachable() -> None:
    preflight = build_mobile_preflight()

    assert preflight.host_class == "loopback"
    assert preflight.iphone_reachable_candidate is False
    assert preflight.requires_allow_non_loopback is False
    assert preflight.public_exposure_risk is False
    assert preflight.service_launch_performed is False
    assert preflight.network_probe_performed is False
    assert preflight.writes_state is False
    assert preflight.runtime_command == "jarvis-codex runtime serve --host 127.0.0.1 --port 8765"
    assert preflight.warnings == ["Loopback is safe for desktop but is not reachable from an iPhone."]


def test_mobile_discovery_recommends_private_interface_without_probe_or_serve() -> None:
    discovery = discover_mobile_hosts(
        interface_records=[
            {
                "ifname": "eth0",
                "flags": ["BROADCAST", "UP"],
                "addr_info": [{"family": "inet", "local": "192.168.1.20"}],
            }
        ]
    )

    assert discovery.status == "READY_FOR_OPERATOR_TEST"
    assert discovery.network_probe_performed is False
    assert discovery.service_launch_performed is False
    assert discovery.browser_opened is False
    assert discovery.writes_state is False
    assert discovery.execution_authority is False
    assert discovery.recommended_candidate is not None
    assert discovery.recommended_candidate.host == "192.168.1.20"
    assert discovery.recommended_candidate.iphone_reachable_candidate is True
    assert "--allow-non-loopback" in discovery.recommended_candidate.runtime_command


def test_mobile_discovery_does_not_recommend_loopback_interface_address() -> None:
    discovery = discover_mobile_hosts(
        interface_records=[
            {
                "ifname": "lo",
                "flags": ["LOOPBACK", "UP"],
                "addr_info": [{"family": "inet", "local": "10.255.255.254"}],
            }
        ]
    )

    assert discovery.status == "NEEDS_PRIVATE_INTERFACE"
    assert discovery.recommended_candidate is None
    assert discovery.candidates[0].iphone_reachable_candidate is False
    assert any("loopback-scoped" in warning for warning in discovery.candidates[0].warnings)


def test_mobile_preflight_classifies_private_network_runtime_command() -> None:
    preflight = build_mobile_preflight("192.168.1.20", 8765)

    assert preflight.host_class == "private-lan"
    assert preflight.iphone_reachable_candidate is True
    assert preflight.requires_allow_non_loopback is True
    assert preflight.public_exposure_risk is False
    assert preflight.url == "http://192.168.1.20:8765"
    assert preflight.runtime_command.endswith("--allow-non-loopback")


def test_mobile_preflight_classifies_tailscale_cgnat() -> None:
    assert classify_mobile_host("100.99.88.77") == "tailscale-cgnat"
    assert build_mobile_preflight("100.99.88.77", 8765).iphone_reachable_candidate is True


def test_mobile_preflight_warns_for_bind_all_and_public_hosts() -> None:
    bind_all = build_mobile_preflight("0.0.0.0", 8765)
    public = build_mobile_preflight("8.8.8.8", 8765)

    assert bind_all.host_class == "bind-all"
    assert bind_all.public_exposure_risk is True
    assert "binds every interface" in bind_all.warnings[0]
    assert public.host_class == "public"
    assert public.public_exposure_risk is True
    assert "separate security review" in public.warnings[0]


def test_mobile_preflight_validates_scheme_and_port() -> None:
    with pytest.raises(ValueError, match="scheme"):
        build_mobile_preflight("127.0.0.1", 8765, "ftp")
    with pytest.raises(ValueError, match="port"):
        build_mobile_preflight("127.0.0.1", 0)


def test_mobile_validation_plan_is_read_only_for_private_network_target() -> None:
    plan = build_mobile_validation_plan("192.168.1.20", 8765)

    assert plan.status == "READY_FOR_OPERATOR_TEST"
    assert plan.target_url == "http://192.168.1.20:8765"
    assert plan.host_class == "private-lan"
    assert plan.iphone_reachable_candidate is True
    assert plan.network_probe_performed is False
    assert plan.service_launch_performed is False
    assert plan.writes_state is False
    assert plan.execution_authority is False
    assert any("microphone permission" in step for step in plan.device_test_steps)
    assert any("operation, risk, and scope" in criterion for criterion in plan.pass_criteria)


def test_mobile_validation_plan_requires_private_target_for_loopback() -> None:
    plan = build_mobile_validation_plan()

    assert plan.status == "NEEDS_PRIVATE_TARGET"
    assert plan.host_class == "loopback"
    assert plan.iphone_reachable_candidate is False
    assert any("not reachable from an iPhone" in warning for warning in plan.warnings)
    assert any("private LAN, Tailscale, or WireGuard" in warning for warning in plan.warnings)


def test_mobile_validation_plan_rejects_public_exposure_as_ready_target() -> None:
    plan = build_mobile_validation_plan("8.8.8.8", 8765)

    assert plan.status == "NEEDS_PRIVATE_TARGET"
    assert plan.host_class == "public"
    assert plan.iphone_reachable_candidate is False
    assert any("public host" in warning for warning in plan.warnings)
    assert any("do not probe the network" in action for action in plan.unsafe_actions)


def test_mobile_evidence_brief_is_read_only_and_release_gate_safe() -> None:
    brief = build_mobile_evidence_brief("192.168.1.20", 8765)

    assert brief.label == "Jarvis mobile operator evidence brief"
    assert brief.status == "READY_FOR_OPERATOR_TEST"
    assert brief.target_url == "http://192.168.1.20:8765"
    assert brief.host_class == "private-lan"
    assert brief.iphone_reachable_candidate is True
    assert brief.public_exposure_risk is False
    assert brief.writes_state is False
    assert brief.network_probe_performed is False
    assert brief.service_launch_performed is False
    assert brief.browser_opened is False
    assert brief.execution_authority is False
    assert brief.release_gate_closed is False
    assert brief.requires_human_acceptance is True
    assert "--allow-non-loopback" in brief.runtime_command
    assert "actual_mobile_device_validation" in brief.release_evidence_command
    assert any("iPhone Safari" in item for item in brief.required_operator_evidence)
    assert any("<state-dir>/release/" in step for step in brief.operator_steps)
    assert any("do not close" in action for action in brief.unsafe_actions)


def test_mobile_evidence_brief_rejects_loopback_as_ready_target() -> None:
    brief = build_mobile_evidence_brief()

    assert brief.status == "NEEDS_PRIVATE_TARGET"
    assert brief.host_class == "loopback"
    assert brief.iphone_reachable_candidate is False
    assert brief.release_gate_closed is False
    assert any("not reachable from an iPhone" in warning for warning in brief.warnings)
