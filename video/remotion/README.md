# Jarvis Codex Remotion Review Assets

Local-only Remotion project for animated review assets that explain the Jarvis Codex plan. It is intentionally isolated under `video/remotion` so it does not change the Python package or introduce hosted publishing.

This scaffold is an asset-generation workspace, not runtime authority. Agents must not run Studio, renders, Docker, GPU paths, or publishing workflows without explicit approval for the exact command and expected writes.

## Setup

```bash
cd video/remotion
npm ci
```

The package pins Remotion to `4.0.481`, matching the currently observed local Remotion version.

## Local Commands

```bash
npm run studio      # open the Remotion Studio locally
npm run still       # write out/jarvis-codex-plan.png
npm run render      # write out/jarvis-codex-plan.mp4
npm run typecheck   # TypeScript validation
```

The default composition is `JarvisCodexPlan` at 1920x1080, 30 fps, 10 seconds.

`npm run studio` starts a local Remotion Studio process. `npm run still`, `npm run render`, and `npm run render:gpu` write files under `out/`. These commands are local-only review commands and are not permission to mutate git, run Worktrunk, execute runtime workflows, or publish assets.

## GPU Notes

Remotion can benefit from GPU acceleration for browser-rendered effects such as transforms, shadows, gradients, filters, WebGL, Skia, P5.js, Mapbox, and many canvas operations. Video encoding itself is not GPU-accelerated by Remotion, and HTML5 or offthread video decoding is not automatically accelerated.

For local rendering with a Chromium mode that can use Linux GPU drivers:

```bash
npm run render:gpu
```

This passes `--gl=angle --chrome-mode=chrome-for-testing`. GPU availability still depends on the host GPU, drivers, Chromium support, and whether Chrome for Testing can access the device.

## Docker Desktop

Docker is optional. Build and render locally:

```bash
docker compose up --build remotion-render
```

Experimental GPU path:

```bash
docker compose --profile gpu up --build remotion-render-gpu
```

Docker Desktop GPU support depends on the host platform and runtime. On Windows, enable WSL2 integration and GPU support for Linux containers before expecting Chromium to see the GPU. If GPU access is unavailable, use the CPU render path.

Docker commands build images and execute rendering workloads. Treat them as explicit approval-gated commands when operated by an agent.

## Publishing Boundary

This scaffold is for local review assets only. It does not configure Remotion Lambda, Cloud Run, Vercel, S3, or any hosted publishing workflow.
