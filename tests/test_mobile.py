from __future__ import annotations

import pytest

from jarvis_codex.mobile import build_mobile_preflight, classify_mobile_host


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
