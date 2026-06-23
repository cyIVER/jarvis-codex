# Electron HUD And Mobile PWA

Jarvis v1 includes a full animated desktop HUD and a private-network mobile PWA.

## Desktop HUD

Use:

- Electron shell.
- React and TypeScript UI.
- xterm.js terminal panes.
- WebGL or Canvas holographic HUD layer.
- ACP-style JSON-RPC runtime client.

The visual direction should feel like a tactical blue holographic assistant:

- Layered translucent panels.
- Circular/radar motifs.
- Dense telemetry bands.
- Status targeting.
- Animated arcs and scanlines.
- Clear text hierarchy and strong contrast.

The visuals must not make operational state ambiguous.

## Required Modes

V1 ships ten modes:

1. Command.
2. Plan.
3. Execute.
4. Adversary.
5. Swarm.
6. Stats.
7. Review.
8. Voice.
9. Memory/Context.
10. Settings/Permissions.

Number keys should switch modes.

## Terminal Panes

Desktop HUD includes managed panes for:

- Codex executor.
- Antigravity planner.
- Dynamic AG adversaries.
- Shell.
- Codeburn stats.

Panes show live output, status, command classification, policy profile, and kill/restart controls.

## Mobile PWA

The iPhone PWA is a private-network client, not a public hosted app.

V1 mobile features:

- Voice button.
- Chat/prompt input.
- Live transcript preview.
- Pending approvals.
- Session status.
- Loop and swarm status.
- Lightweight JARVIS HUD visuals.

Use the same runtime protocol as desktop. Do not build a separate mobile backend.

## Static Viewer Relationship

Existing plan-viewer behavior remains a review surface. The production HUD may reuse concepts from it, but the Electron/PWA harness is the future primary interface.

## Accessibility And Safety

- Keep command approval prompts visually distinct.
- Display when cloud voice is active.
- Display current policy profile.
- Display whether a pane can execute or is read-only.
- Avoid hidden auto-run behavior from UI clicks.

## Acceptance Criteria

- Desktop HUD starts and connects to runtime.
- Mobile PWA connects over private network.
- Ten modes render without layout overlap.
- Terminal panes stream data through runtime-owned PTYs.
- Displayed commands are clearly proposals unless runtime policy executes them.

