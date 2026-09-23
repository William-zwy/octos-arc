#!/usr/bin/env python3
"""Load the generated config with the exact installed Playwright executable."""

import argparse
import os
import subprocess
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from acceptance import AcceptanceRunner


class FailureHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = b'{"error":"controlled missing document"}'
        self.send_response(404)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, _format, *_args):
        pass


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--playwright-root", type=Path, required=True)
    args = parser.parse_args()
    playwright_root = args.playwright_root.resolve()
    executable = playwright_root / "node_modules" / ".bin" / "playwright"
    if os.name == "nt":
        executable = executable.with_suffix(".cmd")
    if not executable.is_file():
        parser.error(f"Playwright executable not found: {executable}")
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        tests = base / "tests"
        tests.mkdir()
        suite = "import { test, expect } from '@playwright/test';\n" + "".join(
            f"test('config loads {index}', async () => expect(true).toBe(true));\n"
            for index in range(1, 35)
        )
        (tests / "REQ-1.spec.ts").write_text(suite, encoding="utf-8")
        runner = AcceptanceRunner(playwright_root, tests, base / "work", print)
        config = runner._prepare(trace_failures=True)
        env = dict(os.environ, NODE_PATH=str(playwright_root / "node_modules"),
                   E2E_BASE_URL="http://127.0.0.1:1", CI="1")
        result = subprocess.run(
            [str(executable), "test", "-c", str(config), "--list"],
            cwd=runner.work_dir, env=env, capture_output=True, text=True,
        )
        output = (result.stdout or "") + (result.stderr or "")
        if result.returncode or "Total: 34 tests" not in output:
            print(output[-2000:])
            return result.returncode or 1
        print("Playwright config gate passed: 34 tests listed")
        server = ThreadingHTTPServer(("127.0.0.1", 0), FailureHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            (tests / "REQ-1.spec.ts").write_text(
                "import { test, expect } from '@playwright/test';\n"
                "test('controlled failure', async ({ page }) => {\n"
                "  await page.goto('/private/alice?token=query-secret');\n"
                "  await expect(page.getByRole('heading', { name: 'Never present' })).toBeVisible();\n"
                "});\n",
                encoding="utf-8",
            )
            summary = runner.run(["REQ-1.spec.ts"], f"http://127.0.0.1:{server.server_port}",
                                 wall_timeout=60, trace_failures=True)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)
        document = summary.results[0].document if summary.results else None
        if (summary.error or summary.total != 1 or summary.passed != 0 or document is None or
                (document.method, document.path, document.status, document.content_type) !=
                ("GET", "/<segment>/<segment>", 404, "application/json") or
                (runner.work_dir / "test-results").exists()):
            print(f"controlled failure gate failed: {summary}")
            return 1
        digest = f"{document.method} {document.path} {document.status} {document.content_type}"
        if "alice" in digest or "query-secret" in digest:
            print(f"controlled failure leaked path/query data: {digest}")
            return 1
        print(f"Controlled failure gate passed: {digest}; raw trace removed")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
