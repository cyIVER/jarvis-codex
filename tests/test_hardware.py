from jarvis_codex.hardware import Accelerator, HardwareProfile, _looks_like_npu, recommend_backend, preflight_check
from pathlib import Path
import json


def profile_with(*accelerators: Accelerator, docker: bool = False) -> HardwareProfile:
    return HardwareProfile(
        system={},
        accelerators=list(accelerators),
        docker={"available": docker},
        recommendations={},
    )


def test_cuda_preferred_for_heavy_workloads():
    profile = profile_with(Accelerator("gpu", "RTX", "cuda", True), docker=True)

    assert recommend_backend(profile, "llm") == "cuda through Docker GPU containers"
    assert recommend_backend(profile, "video") == "cuda through Docker GPU containers"


def test_cuda_without_docker_uses_host_runtime():
    profile = profile_with(Accelerator("gpu", "RTX", "cuda", True), docker=False)

    assert recommend_backend(profile, "video") == "cuda on the host runtime"


def test_video_with_docker_without_cuda_stays_cpu_bound():
    profile = profile_with(docker=True)

    assert recommend_backend(profile, "video") == "dockerized CPU render; enable NVIDIA container runtime for GPU rendering"


def test_npu_preferred_for_voice_and_background_workloads():
    profile = profile_with(Accelerator("npu", "Intel AI Boost", "windows-directml-openvino", True))

    assert recommend_backend(profile, "voice") == "windows-npu via ONNX Runtime DirectML or OpenVINO adapter"
    assert recommend_backend(profile, "background") == "windows-npu via ONNX Runtime DirectML or OpenVINO adapter"


def test_cpu_fallback_mentions_future_npu_for_voice():
    profile = profile_with()

    assert recommend_backend(profile, "voice") == "cpu now; prefer NPU when a Windows ONNX/OpenVINO adapter is configured"


def test_npu_matching_does_not_confuse_input_devices():
    assert _looks_like_npu("Intel(R) AI Boost")
    assert _looks_like_npu("Neural Processing Unit")
    assert not _looks_like_npu("USB Input Device")
    assert not _looks_like_npu("Microsoft Input Configuration Device")

def test_preflight_check_deny_path(tmp_path):
    profile = profile_with(Accelerator("gpu", "RTX", "cuda", True))
    state_dir = tmp_path / "state"
    
    # Run preflight without approval
    decision = preflight_check(profile, "llm", state_dir)
    assert decision["recommended_backend"].startswith("cuda")
    assert decision["needs_approval"] is True
    assert decision["approved"] is False
    assert decision["can_proceed"] is False
    
    # Check that it logged the decision
    log_file = state_dir / "logs" / "hardware_gate_checks.jsonl"
    assert log_file.exists()
    
    # Add approval flag
    flag_path = state_dir / "approvals" / "hardware_flag.json"
    flag_path.parent.mkdir(parents=True, exist_ok=True)
    flag_path.write_text(json.dumps({"approved": True}))
    
    # Run preflight again
    decision2 = preflight_check(profile, "llm", state_dir)
    assert decision2["approved"] is True
    assert decision2["can_proceed"] is True
