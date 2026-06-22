#!/usr/bin/env python3
"""Validate Jarvis Phase 1 project-local Codex governance files.

This validator is intentionally stdout-only. It writes no reports and mutates no
repository or global Codex state.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from jarvis_codex.governance import main


if __name__ == "__main__":
    raise SystemExit(main())
