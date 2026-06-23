# Mobile Access

Jarvis v1 supports iPhone access through a private-network PWA.

Native iOS is planned future scope.

## V1 Access Model

- Jarvis runtime stays on the Windows/WSL machine.
- Electron desktop uses loopback.
- iPhone connects over Tailscale or WireGuard.
- Mobile UI is a PWA served by the local runtime.
- No public internet exposure is enabled by default.

## Mobile Features

V1 PWA includes:

- Voice button.
- Transcript preview.
- Chat/prompt input.
- Pending approvals.
- Session and loop status.
- Swarm status.
- Compact Codeburn stats.
- Lightweight JARVIS visual style.

## Security Rules

- Private-network access must be explicitly enabled.
- Runtime should bind to loopback unless mobile mode is enabled.
- Mobile sessions are separate clients with their own session IDs.
- Mobile approvals must show the same action details as desktop.
- Public tunnel support is not v1.

## Native iOS Future Scope

Future native iOS client may add:

- Push notifications.
- Better background voice behavior.
- Native audio controls.
- Secure enclave or keychain integration.
- App-store style distribution.

This requires Apple signing and either macOS/Xcode or a cloud build service. It should reuse the same ACP-style runtime protocol.

## Acceptance Criteria

- iPhone PWA can connect over private VPN.
- PWA can submit voice/text prompts.
- PWA can approve or reject pending gated actions.
- Runtime does not expose a public interface by default.

