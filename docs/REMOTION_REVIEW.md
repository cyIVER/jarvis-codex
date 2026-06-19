# Remotion Review Gate

Remotion is a future local-only review asset path. Gate 2 does not add Remotion dependencies or video generation.

## Before Implementation

- Define the review objective and target audience.
- Keep Remotion dependencies project-local.
- Store generated videos, frames, and temporary render artifacts outside Git.
- Verify browser playback and rendered frames locally.
- Ask for approval before GPU/Docker execution, dependency installation, or long-running renders.

## Candidate Assets

| Asset | Purpose | Gate |
| --- | --- | --- |
| Short plan walkthrough | Show the selected Gate 2 next steps | Requires local-only storyboard approval |
| Lane reconciliation clip | Explain Worktrunk lane states | Requires lane refresh decision |
| Hardware boundary clip | Show CUDA/NPU/Docker routing | Requires runtime execution approval |

## Acceptance Checks

- Remotion project scaffold is explicit and reversible.
- Render output path is ignored by Git.
- Browser smoke confirms the review asset loads locally.
- No hosted publish path is added without explicit approval.
