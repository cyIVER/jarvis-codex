@echo off
setlocal

set "JARVIS_DISTRO=%JARVIS_WSL_DISTRO%"
set "JARVIS_REPO=%JARVIS_WSL_REPO%"
if "%JARVIS_REPO%"=="" set "JARVIS_REPO=/home/iveri/repos/jarvis-codex"

if "%JARVIS_DISTRO%"=="" (
  wsl.exe --cd "%JARVIS_REPO%" -- bash -lc "command -v jarvis >/dev/null 2>&1 && exec jarvis %* || exec uv run jarvis %*"
) else (
  wsl.exe -d "%JARVIS_DISTRO%" --cd "%JARVIS_REPO%" -- bash -lc "command -v jarvis >/dev/null 2>&1 && exec jarvis %* || exec uv run jarvis %*"
)

endlocal
