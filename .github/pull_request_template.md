## Summary

- 

## Validation

- [ ] `uv run pytest`
- [ ] `python3 scripts/validate-jarvis-codex-phase1.py`
- [ ] Remotion checks, if review assets changed: `npm run typecheck` and `npm audit --audit-level=high`

## Safety Boundaries

- [ ] No Worktrunk mutation, git mutation, service launch, Docker/GPU workload, local ML runtime, install, migration, or daemon execution is bundled without explicit approval.
- [ ] Displayed commands remain display-only unless a separate approval authorizes execution.
- [ ] Generated Remotion outputs remain local ignored review assets unless release packaging is explicitly approved.
