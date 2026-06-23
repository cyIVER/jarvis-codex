---
name: harness-evaluator
description: "Evaluates proposed codebase changes against the AGENTS.md Ratchet rules to act as an Inferential Sensor."
---

# Purpose
This skill implements the "LLM as Judge" pattern (Inferential Sensor) to prevent agents from "grading their own homework." It evaluates proposals against `AGENTS.md` Ratchet rules.

# When to use
Use before an agent commits or executes a major CLI handoff.

# When not to use
Do not use for trivial tasks or simple file readings.

# Tool expectations
Requires file read access to `AGENTS.md`. No write access required.

# Workflow
1. Read the current `AGENTS.md` file (especially the Ratchet).
2. Review the proposed diff, plan, or CLI command.
3. Evaluate against constraints.

# Expected output
Output "HARNESS_CHECK_PASSED" if safe. Output "HARNESS_CHECK_FAILED" with the violated rule if unsafe.

# Guardrails
Do not automatically approve proposals; be highly critical.

# Validation
Validation is done manually or by the generator agent reading the verbose output and self-correcting.
