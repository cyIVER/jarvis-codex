from __future__ import annotations

import json
import os
import platform
import re
import shutil
import subprocess
from dataclasses import asdict, dataclass
from typing import Any, Literal

Workload = Literal["general", "llm", "vision", "voice", "video", "background"]


@dataclass(frozen=True)
class Accelerator:
    kind: str
    name: str
    backend: str
    available: bool
    detail: str = ""


@dataclass(frozen=True)
class HardwareProfile:
    system: dict[str, Any]
    accelerators: list[Accelerator]
    docker: dict[str, Any]
    recommendations: dict[str, str]

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["accelerators"] = [asdict(item) for item in self.accelerators]
        return data


def inspect_hardware() -> HardwareProfile:
    accelerators: list[Accelerator] = []
    accelerators.extend(_nvidia_accelerators())
    accelerators.extend(_windows_npu_accelerators())
    accelerators.extend(_wsl_accelerators())

    profile = HardwareProfile(
        system={
            "platform": platform.platform(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "cpu_count": os.cpu_count(),
            "wsl": _is_wsl(),
        },
        accelerators=accelerators,
        docker=_docker_status(),
        recommendations={},
    )
    return HardwareProfile(
        system=profile.system,
        accelerators=profile.accelerators,
        docker=profile.docker,
        recommendations={workload: recommend_backend(profile, workload) for workload in _workloads()},
    )


def recommend_backend(profile: HardwareProfile, workload: Workload = "general") -> str:
    has_cuda = any(item.available and item.backend == "cuda" for item in profile.accelerators)
    has_npu = any(item.available and item.kind == "npu" for item in profile.accelerators)
    has_docker = bool(profile.docker.get("available"))

    if workload in {"llm", "vision", "video"} and has_cuda:
        container_note = " through Docker GPU containers" if has_docker else " on the host runtime"
        return f"cuda{container_note}"
    if workload in {"voice", "background"} and has_npu:
        return "windows-npu via ONNX Runtime DirectML or OpenVINO adapter"
    if workload == "video" and has_docker:
        return "dockerized CPU render; enable NVIDIA container runtime for GPU rendering"
    if workload in {"voice", "background"}:
        return "cpu now; prefer NPU when a Windows ONNX/OpenVINO adapter is configured"
    return "cpu"


def _nvidia_accelerators() -> list[Accelerator]:
    if not shutil.which("nvidia-smi"):
        return []
    result = _run(
        [
            "nvidia-smi",
            "--query-gpu=name,memory.total,driver_version",
            "--format=csv,noheader",
        ]
    )
    if result.returncode != 0:
        return [Accelerator(kind="gpu", name="NVIDIA GPU", backend="cuda", available=False, detail=result.stderr.strip())]

    accelerators: list[Accelerator] = []
    for line in result.stdout.splitlines():
        parts = [part.strip() for part in line.split(",")]
        if not parts or not parts[0]:
            continue
        cuda_version = _nvidia_cuda_version()
        detail_parts = [part for part in parts[1:] if part]
        if cuda_version:
            detail_parts.append(f"CUDA {cuda_version}")
        detail = ", ".join(detail_parts)
        accelerators.append(Accelerator(kind="gpu", name=parts[0], backend="cuda", available=True, detail=detail))
    return accelerators


def _windows_npu_accelerators() -> list[Accelerator]:
    if not shutil.which("powershell.exe"):
        return []
    script = r"""
$devices = Get-PnpDevice | Where-Object {
  $_.FriendlyName -match 'NPU|Neural|AI Boost|VPU|Inference|NNA' -or
  $_.Class -match 'NPU|Compute|System'
} | Select-Object Class,FriendlyName,Status,InstanceId
$devices | ConvertTo-Json -Depth 3
"""
    result = _run(["powershell.exe", "-NoProfile", "-Command", script], timeout=8)
    if result.returncode != 0 or not result.stdout.strip():
        return []
    try:
        raw = json.loads(result.stdout)
    except json.JSONDecodeError:
        return []
    devices = raw if isinstance(raw, list) else [raw]
    accelerators: list[Accelerator] = []
    for device in devices:
        if not isinstance(device, dict):
            continue
        name = str(device.get("FriendlyName") or "")
        if not _looks_like_npu(name):
            continue
        status = str(device.get("Status") or "")
        accelerators.append(
            Accelerator(
                kind="npu",
                name=name,
                backend="windows-directml-openvino",
                available=status.lower() == "ok",
                detail=f"status={status}; class={device.get('Class')}",
            )
        )
    return accelerators


def _wsl_accelerators() -> list[Accelerator]:
    accelerators: list[Accelerator] = []
    if os.path.exists("/dev/dxg"):
        accelerators.append(
            Accelerator(
                kind="wsl-gpu-bridge",
                name="/dev/dxg",
                backend="wsl-directx",
                available=True,
                detail="WSL DirectX bridge present; CUDA may be exposed through the Windows driver.",
            )
        )
    return accelerators


def _docker_status() -> dict[str, Any]:
    if not shutil.which("docker"):
        return {"available": False, "detail": "docker command not found"}
    result = _run(["docker", "version", "--format", "{{json .}}"], timeout=8)
    if result.returncode != 0:
        return {"available": False, "detail": result.stderr.strip() or result.stdout.strip()}
    try:
        parsed = json.loads(result.stdout)
    except json.JSONDecodeError:
        parsed = {}
    return {
        "available": True,
        "client_version": parsed.get("Client", {}).get("Version"),
        "server_version": parsed.get("Server", {}).get("Version"),
    }


def _run(args: list[str], timeout: int = 5) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, capture_output=True, text=True, timeout=timeout, check=False)


def _is_wsl() -> bool:
    release = platform.release().lower()
    return "microsoft" in release or "wsl" in release


def _looks_like_npu(name: str) -> bool:
    lowered = name.lower()
    return bool(re.search(r"\b(npu|vpu|nna)\b", lowered)) or any(
        token in lowered for token in ("neural", "ai boost", "inference")
    )


def _nvidia_cuda_version() -> str:
    result = _run(["nvidia-smi"], timeout=5)
    if result.returncode != 0:
        return ""
    match = re.search(r"CUDA Version:\s*([0-9.]+)", result.stdout)
    return match.group(1) if match else ""


def _workloads() -> tuple[Workload, ...]:
    return ("general", "llm", "vision", "voice", "video", "background")
