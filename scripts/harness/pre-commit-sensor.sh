#!/usr/bin/env bash

# Harness Engineering: Computational Sensor
# This pre-commit hook acts as a deterministic feedback sensor.
# "Success is silent, failures are verbose."

REPO_DIR=$(git rev-parse --show-toplevel)

echo "[Sensor] Validating Jarvis Phase 1 Governance..."
python3 "$REPO_DIR/scripts/validate-jarvis-codex-phase1.py"

if [ $? -ne 0 ]; then
    echo ""
    echo "==============================================="
    echo "[Harness Error] The computational sensor failed!"
    echo "The agent attempted a change that violates governance."
    echo "Please self-correct the issue before committing."
    echo "==============================================="
    exit 1
fi

# Additional computational sensors can be added here.
exit 0
