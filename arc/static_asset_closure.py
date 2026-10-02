"""Deterministic checks for generated app static-asset closure.

This module is intentionally app-side: it never changes the Agent ZIP contract.
It validates local script/link references after a frontend build and provides a
small runtime probe for the already-running acceptance server.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit
import http.client
import re


class _ReferenceParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.references: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "script" and values.get("src"):
            self.references.append(values["src"] or "")
        if tag == "link" and values.get("href") and values.get("rel", "").lower() in {"stylesheet", "icon", "manifest"}:
            self.references.append(values["href"] or "")


def referenced_assets(index_html: Path) -> list[str]:
    parser = _ReferenceParser()
    parser.feed(index_html.read_text(encoding="utf-8", errors="replace"))
    return parser.references


def _local_path(reference: str) -> str | None:
    parsed = urlsplit(reference)
    if parsed.scheme or parsed.netloc or reference.startswith(("data:", "blob:", "#")):
        return None
    path = parsed.path or "/"
    if "{" in path or "}" in path or "<" in path or ">" in path:
        return None
    return path


def check_static_closure(project: Path) -> dict:
    """Check built frontend references without assuming a specific bundler."""
    frontend = project / "frontend"
    index = frontend / "dist" / "index.html"
    if not index.is_file():
        index = frontend / "index.html"
    if not index.is_file():
        return {"status": "inconclusive", "entrypoints": [], "local_references": [],
                "missing_assets": ["index.html"], "unsafe_external_references": [],
                "dynamic_references": [], "runtime_probe_required": True}
    refs = referenced_assets(index)
    missing: list[str] = []
    local: list[str] = []
    dynamic: list[str] = []
    for ref in refs:
        path = _local_path(ref)
        if path is None:
            if ref.startswith(("http://", "https://", "//")):
                continue
            if any(ch in ref for ch in "{}<>"):
                dynamic.append(ref)
            continue
        local.append(path)
        rel = path.lstrip("/") or "index.html"
        candidate = index.parent / rel
        try:
            candidate.resolve().relative_to(index.parent.resolve())
        except ValueError:
            missing.append(path)
            continue
        if candidate.is_dir():
            candidate = candidate / "index.html"
        if not candidate.is_file():
            missing.append(path)
    return {"status": "passed" if not missing else "failed", "entrypoints": [str(index)],
            "local_references": local, "missing_assets": sorted(set(missing)),
            "unsafe_external_references": [], "dynamic_references": dynamic,
            "runtime_probe_required": True}


def probe_runtime_assets(port: int, paths: list[str], timeout: float = 4.0) -> str | None:
    """Return a concise failure for the first non-2xx/3xx local asset."""
    for path in paths:
        try:
            conn = http.client.HTTPConnection("127.0.0.1", port, timeout=timeout)
            conn.request("GET", path)
            response = conn.getresponse()
            response.read()
            status = response.status
            conn.close()
        except Exception as exc:  # noqa: BLE001
            return f"static asset probe GET {path} failed: {exc.__class__.__name__}"
        if status < 200 or status >= 400:
            return f"static asset probe GET {path} returned HTTP {status}"
    return None
