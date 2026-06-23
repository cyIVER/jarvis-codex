from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree


ROOT = Path(__file__).resolve().parents[1]
WINDOWS_MIC = ROOT / "tools" / "windows-mic"
PROJECT = WINDOWS_MIC / "JarvisMicRecorder" / "JarvisMicRecorder.csproj"
PROGRAM = WINDOWS_MIC / "JarvisMicRecorder" / "Program.cs"


def test_windows_mic_project_targets_windows_and_pins_audio_dependency() -> None:
    project = ElementTree.fromstring(PROJECT.read_text(encoding="utf-8"))
    property_group = project.find("PropertyGroup")
    assert property_group is not None
    properties = {child.tag: child.text for child in property_group}
    package_refs = {
        item.attrib["Include"]: item.attrib["Version"]
        for item in project.findall("ItemGroup/PackageReference")
    }

    assert properties["OutputType"] == "Exe"
    assert properties["TargetFramework"] == "net10.0-windows"
    assert properties["RuntimeIdentifier"] == "win-x64"
    assert properties["SelfContained"] == "false"
    assert package_refs == {"NAudio": "2.2.1"}


def test_windows_mic_program_implements_adapter_contract_and_bounds() -> None:
    program = PROGRAM.read_text(encoding="utf-8")

    assert "--output-file" in program
    assert "--seconds" in program
    assert "MinSeconds = 1" in program
    assert "MaxSeconds = 300" in program
    assert "WaveFileWriter.CreateWaveFile16" in program
    assert "TargetSampleRate = 16000" in program
    assert "WasapiCapture" in program
    assert "shell" not in program.lower()


def test_windows_mic_wrapper_converts_wsl_paths_and_invokes_recorder() -> None:
    wrapper = (WINDOWS_MIC / "jarvis-record.ps1").read_text(encoding="utf-8")

    assert "--output-file" in wrapper
    assert "--seconds" in wrapper
    assert "wsl.exe wslpath -w" in wrapper
    assert "JARVIS_MIC_RECORDER_EXE" in wrapper
    assert "JarvisMicRecorder.exe" in wrapper
    assert "& $recorder @recorderArgs" in wrapper


def test_windows_mic_docs_state_foreground_local_boundaries() -> None:
    readme = (WINDOWS_MIC / "README.md").read_text(encoding="utf-8")

    assert "Foreground command only." in readme
    assert "No background listener." in readme
    assert "No wake word." in readme
    assert "No network calls." in readme
    assert "No cloud speech-to-text fallback." in readme
    assert "No command execution authority." in readme
    assert "JARVIS_RECORD_COMMAND" in readme


def test_gitignore_excludes_windows_mic_build_outputs() -> None:
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")

    assert "tools/windows-mic/**/bin/" in gitignore
    assert "tools/windows-mic/**/obj/" in gitignore
