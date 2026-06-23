#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import mimetypes
import os
import posixpath
import sys
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse


ROOT = Path(__file__).resolve().parents[1]
STATIC_DIR = ROOT / "tools" / "plan-viewer"
DEFAULT_PLANS_DIR = ROOT / "plans" / "jarvis-codex-swarm"


class PlanViewerHandler(SimpleHTTPRequestHandler):
    static_dir: Path
    plans_dir: Path

    def log_message(self, format: str, *args: object) -> None:
        sys.stderr.write("[plan-viewer] " + format % args + "\n")

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = unquote(parsed.path)
        if path == "/api/plans":
            self._send_plan_index()
            return
        if path.startswith("/api/plans/"):
            self._send_plan_file(path.removeprefix("/api/plans/"))
            return
        self._send_static(path)

    def _send_json(self, payload: object, status: int = 200) -> None:
        data = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_plan_index(self) -> None:
        plans = []
        if self.plans_dir.exists():
            for path in sorted(self.plans_dir.glob("*")):
                if path.is_file() and path.suffix.lower() in {".md", ".mdx"}:
                    stat = path.stat()
                    plans.append(
                        {
                            "name": path.name,
                            "size": stat.st_size,
                            "mtime": int(stat.st_mtime),
                            "url": f"/api/plans/{path.name}",
                        }
                    )
        self._send_json({"plans_dir": str(self.plans_dir), "plans": plans})

    def _send_plan_file(self, name: str) -> None:
        clean_name = posixpath.basename(name)
        path = (self.plans_dir / clean_name).resolve()
        if not self._is_inside(path, self.plans_dir) or path.suffix.lower() not in {
            ".md",
            ".mdx",
        }:
            self._send_json({"error": "Plan path is outside the served directory."}, 403)
            return
        if not path.exists() or not path.is_file():
            self._send_json({"error": "Plan not found."}, 404)
            return
        stat = path.stat()
        self._send_json(
            {
                "name": path.name,
                "size": stat.st_size,
                "mtime": int(stat.st_mtime),
                "content": path.read_text(encoding="utf-8"),
            }
        )

    def _send_static(self, request_path: str) -> None:
        if request_path in {"", "/"}:
            request_path = "/index.html"
        relative = request_path.lstrip("/")
        path = (self.static_dir / relative).resolve()
        if not self._is_inside(path, self.static_dir) or not path.is_file():
            self.send_error(404, "Not found")
            return
        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        data = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    @staticmethod
    def _is_inside(path: Path, parent: Path) -> bool:
        try:
            path.relative_to(parent.resolve())
            return True
        except ValueError:
            return False


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Serve the local Jarvis Codex plan viewer.")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host")
    parser.add_argument("--port", type=int, default=8765, help="Bind port")
    parser.add_argument(
        "--plans",
        default=str(DEFAULT_PLANS_DIR),
        help="Directory containing .md or .mdx plans",
    )
    parser.add_argument("--open", action="store_true", help="Open the viewer in a browser")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    static_dir = STATIC_DIR.resolve()
    plans_dir = Path(args.plans).expanduser()
    if not plans_dir.is_absolute():
        plans_dir = ROOT / plans_dir
    plans_dir = plans_dir.resolve()

    if not static_dir.exists():
        print(f"Static viewer directory not found: {static_dir}", file=sys.stderr)
        return 2
    if not plans_dir.exists():
        print(f"Plans directory not found: {plans_dir}", file=sys.stderr)
        return 2

    PlanViewerHandler.static_dir = static_dir
    PlanViewerHandler.plans_dir = plans_dir
    server = ThreadingHTTPServer((args.host, args.port), PlanViewerHandler)
    url = f"http://{args.host}:{server.server_port}/"
    print(f"Serving Jarvis Codex plan viewer at {url}")
    print(f"Plans directory: {plans_dir}")
    if args.open:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping plan viewer.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    os.chdir(ROOT)
    raise SystemExit(main())
