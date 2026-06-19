from jarvis_codex.hardware import Accelerator, HardwareProfile, _looks_like_npu, recommend_backend


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
