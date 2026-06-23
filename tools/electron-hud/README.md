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

Reviewed packaging scripts are present for a future local package/signing phase:

```bash
npm run package
npm run make
```

These commands write package artifacts under the ignored `tools/electron-hud/dist/` directory. They do not imply signing, distribution approval, runtime launch, or artifact publication.

The non-signing unpacked Linux package path has been locally validated with `npm run package`. The generated `dist/` contents are local evidence only and must remain uncommitted unless a later release-artifact plan explicitly approves them.

The unsigned Linux AppImage path has also been locally validated with `npm run make`. The generated AppImage is local evidence only. It is not signed, reviewed for distribution, copied to a release location, or publication-ready.

The Electron Builder config uses the committed `assets/icon.png` package icon. Local `npm run make` validation no longer emits the default Electron icon warning.

Safety boundaries:

- Loads `http://127.0.0.1:8765` by default.
- `package-lock.json` pins Electron dependency resolution; it does not mean dependencies are installed.
- `node_modules` is a local setup artifact only and is ignored by git.
- `electron-builder.json` and the `package`/`make` scripts define a reviewed local packaging path; package execution, signing, and artifact copy remain separate approval-gated actions.
- `assets/icon.png` is package metadata only; it does not approve signing, artifact copy, publication, or distribution.
- Local `dist/` artifacts are validation evidence only; they are not signed release artifacts and are not publication-ready.
- Non-loopback runtime URLs require `JARVIS_ELECTRON_ALLOW_NON_LOOPBACK=1` and should be treated as an explicit private-network operator decision.
- Renderer Node integration is disabled.
- Context isolation and sandboxing are enabled.
- New windows and cross-origin navigation are denied.
- Microphone permission is allowed only for the configured runtime origin.
- The Electron shell does not execute commands. Runtime policy, approvals, PTYs, and voice adapters remain owned by the Jarvis runtime.
