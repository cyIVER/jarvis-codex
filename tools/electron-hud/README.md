# Jarvis Electron HUD

This is a local-only Electron shell for the Jarvis runtime HUD.

Start the runtime separately:

```bash
jarvis-codex runtime serve
```

The dependency lockfile is committed. It was generated with lifecycle scripts disabled.

Local dependencies may be installed under ignored `tools/electron-hud/node_modules/` for operator validation. Do not commit `node_modules`.

Then, from this directory after installing the Electron dependency in a separately approved setup step:

```bash
npm start
```

Safety boundaries:

- Loads `http://127.0.0.1:8765` by default.
- `package-lock.json` pins Electron dependency resolution; it does not mean dependencies are installed.
- `node_modules` is a local setup artifact only and is ignored by git.
- Dependency installation, packaging, signing, and artifact copy remain separate approval-gated actions.
- Non-loopback runtime URLs require `JARVIS_ELECTRON_ALLOW_NON_LOOPBACK=1` and should be treated as an explicit private-network operator decision.
- Renderer Node integration is disabled.
- Context isolation and sandboxing are enabled.
- New windows and cross-origin navigation are denied.
- Microphone permission is allowed only for the configured runtime origin.
- The Electron shell does not execute commands. Runtime policy, approvals, PTYs, and voice adapters remain owned by the Jarvis runtime.
