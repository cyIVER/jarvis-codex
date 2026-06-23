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
- Use `jarvis-codex mobile discover --json` to list local private-network host candidates without starting the runtime, probing the network, opening browsers, or writing state.
- The HUD runtime readiness panel also displays the recommended mobile candidate, proposed runtime serve command, preflight command, and validation-plan command from the same non-writing discovery path.
- Use `jarvis-codex mobile preflight --host <private-ip-or-vpn-ip> --json` before serving a non-loopback runtime.
- The mobile preflight is read-only. It does not launch services, probe the network, write state, or prove that an iPhone can connect.
- Use `jarvis-codex mobile validation-plan --host <private-ip-or-vpn-ip> --json` to prepare the operator evidence checklist for a real iPhone/PWA validation session.
- Use `jarvis-codex mobile evidence-brief --host <private-ip-or-vpn-ip> --json` to package the target URL, approval-gated serve command, required screenshots/notes, and release-evidence recording command into one read-only operator brief.
- On this WSL host, discovery currently recommends `172.28.39.152` as the private-interface candidate. Treat this as local evidence only; the operator still has to approve the serve command and verify reachability from the iPhone.
- The validation-plan and evidence-brief commands are read-only. They do not launch the runtime, open a browser, contact the phone, probe the network, write state, close release gates, or grant permission to execute displayed commands.
- HUD-displayed mobile commands are display-only proposals. They are not buttons, shell execution, Worktrunk execution, git execution, local ML execution, service launch authority, or approval to bind non-loopback.
- Mobile sessions are separate clients with their own session IDs.
- Mobile approvals must show the same action details as desktop.
- Public tunnel support is not v1.

## Device Validation Evidence

A real iPhone validation session should capture evidence outside the CLI:

- Screenshot of iPhone Safari loading the Jarvis HUD URL.
- Confirmation that PWA install or standalone launch works when tested.
- Confirmation that microphone permission appears only after tapping the microphone control.
- Screenshot or note showing approval cards expose operation, risk, and scope.
- Note that the runtime was served only on an approved private-network address.

The validation plan is not execution authority. Starting the runtime, binding to a non-loopback address, running Worktrunk, running git commands, starting local ML, starting Docker, launching services, or running daemons still requires a separate explicit approval for the exact action.

The evidence brief is also not validation proof. It helps the operator collect and record evidence, but `actual_mobile_device_validation` remains open until a human accepts the iPhone evidence.

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
- Operator evidence is captured for URL reachability, microphone click-to-arm behavior, approval-card scope, and private-network binding.
