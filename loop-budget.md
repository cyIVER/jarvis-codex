# Loop Budget - Jarvis Codex

This budget constrains the Product Readiness Triage loop described in `LOOP.md`.

## Default Budget

| Limit | Value |
| --- | --- |
| Target level | L1 |
| Default cadence | manual/operator-requested |
| Maximum autonomous package size | one coherent commit group |
| Preferred validation before commit | targeted test, full `uv run pytest`, governance validator |
| Suggested token cap per loop cycle | 120k |
| Suggested wall-clock review checkpoint | after each commit |

## Cost Estimate

`loop-cost` for the generic daily-triage L1 pattern reported:

- no-op run: 5k tokens
- full triage: 50k tokens
- action run: 200k tokens
- realistic daily blend at high cadence: 276k tokens

Jarvis Codex therefore does not run this loop on an unattended high-frequency cadence. It runs manually or when the operator asks to continue.

## Kill Switches

Stop the loop when:

- `STATE.md` has `loop_status: paused`
- the same validation failure repeats three times
- a runtime, service, Docker, GPU, local ML, Worktrunk mutation, or destructive git action is needed
- package scope crosses more than one product slice
- the user asks to stop

## Escalation Rules

Escalate before:

- adding command runners
- exposing lane mutation through CLI
- adding voice ingress runtime bridges
- changing global Codex agents, skills, MCPs, memory, or approval policy
- weakening project-local governance boundaries
