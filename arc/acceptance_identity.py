"""Fail-closed identity routing for bundled ARC acceptance suites."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


IDENTITY_MANIFEST = "manifest.json"


class AcceptanceIdentityError(RuntimeError):
    """Acceptance tests could not be tied to exactly one trusted task identity."""

    def __init__(self, status: str, detail: str, audit: dict | None = None):
        super().__init__(f"{status}: {detail}")
        self.status = status
        self.audit = audit or {"status": status, "detail": detail}


@dataclass(frozen=True)
class AcceptanceSelection:
    path: Path
    audit: dict


def _text(value: object) -> str:
    return str(value or "").replace("\r\n", "\n").replace("\r", "\n")


def _canonical_scenario(value: object) -> dict:
    scenario = value if isinstance(value, dict) else {}
    steps = []
    for raw in scenario.get("steps") or []:
        step = raw if isinstance(raw, dict) else {}
        steps.append({"keyword": _text(step.get("keyword")), "content": _text(step.get("content"))})
    return {"name": _text(scenario.get("name")), "steps": steps}


def canonical_requirement_tree(tree: dict) -> dict:
    """Keep semantic requirement fields while ignoring YAML byte representation."""
    if not isinstance(tree, dict):
        raise ValueError("requirement tree must be an object")
    children = [canonical_requirement_tree(child) for child in tree.get("children") or []]
    return {
        "id": _text(tree.get("id")),
        "name": _text(tree.get("name")),
        "type": _text(tree.get("type")),
        "description": _text(tree.get("description")),
        "dependencies": sorted(_text(item) for item in (tree.get("dependencies") or [])),
        "scenarios": [_canonical_scenario(item) for item in (tree.get("scenarios") or [])],
        "children": children,
    }


def requirement_fingerprint(tree: dict) -> str:
    payload = json.dumps(canonical_requirement_tree(tree), ensure_ascii=False, sort_keys=True,
                         separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest().upper()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def inspect_suite(path: Path) -> dict:
    specs = sorted(path.rglob("*.spec.ts")) if path.is_dir() else []
    helper = path / "helpers.ts"
    spec_entries = [{"path": item.relative_to(path).as_posix(), "sha256": _sha256(item)} for item in specs]
    encoded = json.dumps(spec_entries, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {
        "spec_count": len(spec_entries),
        "spec_files": [entry["path"] for entry in spec_entries],
        "specs_sha256": hashlib.sha256(encoded).hexdigest().upper(),
        "helper_sha256": _sha256(helper) if helper.is_file() else None,
    }


def _load_manifest(bundle_dir: Path) -> list[dict]:
    path = bundle_dir / "public-tests" / IDENTITY_MANIFEST
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        raise AcceptanceIdentityError("acceptance_identity_invalid", f"manifest unreadable: {exc}") from exc
    if not isinstance(raw, dict) or raw.get("schema_version") != 2 or not isinstance(raw.get("suites"), list):
        raise AcceptanceIdentityError("acceptance_identity_invalid", "manifest schema must be version 2")
    required = {"suite_path", "task_key", "competition", "snapshot", "requirements_fingerprint",
                "spec_count", "specs_sha256", "helper_sha256"}
    suites = raw["suites"]
    if any(not isinstance(item, dict) or not required.issubset(item) for item in suites):
        raise AcceptanceIdentityError("acceptance_identity_invalid", "manifest suite entry is incomplete")
    keys = [str(item["task_key"]) for item in suites]
    if len(keys) != len(set(keys)):
        raise AcceptanceIdentityError("acceptance_identity_ambiguous", "manifest contains duplicate task keys")
    return suites


def _task_key_from_inputs(tree: dict, req_dir: Path, known_keys: set[str]) -> tuple[str | None, str]:
    for field in ("task_key", "taskKey"):
        value = tree.get(field)
        if isinstance(value, str) and value in known_keys:
            return value, f"requirements.{field}"
    for part in reversed(req_dir.resolve().parts):
        if part in known_keys:
            return part, "requirement_path"
    return None, "unavailable"


def _entry_matches_suite(entry: dict, observed: dict) -> bool:
    return all(observed.get(field) == entry.get(field)
               for field in ("spec_count", "specs_sha256", "helper_sha256"))


def _audit(entry: dict, req_fp: str, task_input: str, source: str, path: Path, observed: dict) -> dict:
    return {
        "status": "selected",
        "source": source,
        "suite_path": entry["suite_path"],
        "selected_path": str(path.resolve()),
        "selection_basis": "task_key" if task_input != "unavailable" else "requirements_fingerprint",
        "task_key_input": task_input,
        "task_key": entry["task_key"],
        "competition": entry["competition"],
        "snapshot": entry["snapshot"],
        "requirements_fingerprint": req_fp,
        "helper_sha256": observed["helper_sha256"],
        "specs_sha256": observed["specs_sha256"],
        "spec_count": observed["spec_count"],
        "spec_files": observed["spec_files"],
    }


def locate_acceptance_suite(tree: dict, req_dir: Path, bundle_dir: Path,
                            platform_candidates: list[Path], logger: Callable[[str], None]) -> AcceptanceSelection:
    suites = _load_manifest(bundle_dir)
    known = {str(item["task_key"]) for item in suites}
    task_key, task_input = _task_key_from_inputs(tree, req_dir, known)
    req_fp = requirement_fingerprint(tree)
    matches = ([item for item in suites if item["task_key"] == task_key] if task_key else
               [item for item in suites if item["requirements_fingerprint"] == req_fp])
    if len(matches) != 1:
        audit = {"status": "acceptance_identity_ambiguous", "task_key_input": task_input,
                 "task_key": task_key, "requirements_fingerprint": req_fp,
                 "matching_suites": [item["suite_path"] for item in matches]}
        raise AcceptanceIdentityError("acceptance_identity_ambiguous",
                                      f"expected one exact suite, found {len(matches)}", audit)
    entry = matches[0]
    if entry["requirements_fingerprint"] != req_fp:
        audit = {"status": "acceptance_identity_mismatch", "task_key_input": task_input,
                 "task_key": task_key, "expected_fingerprint": entry["requirements_fingerprint"],
                 "requirements_fingerprint": req_fp}
        raise AcceptanceIdentityError("acceptance_identity_mismatch",
                                      "explicit task key disagrees with requirements fingerprint", audit)

    for candidate in platform_candidates:
        observed = inspect_suite(candidate)
        if not observed["spec_count"]:
            logger(f"[tests] platform candidate {candidate}: no *.spec.ts")
            continue
        if not _entry_matches_suite(entry, observed):
            other = [item["task_key"] for item in suites if _entry_matches_suite(item, observed)]
            audit = {"status": "acceptance_identity_mismatch", "source": "platform",
                     "candidate": str(candidate), "expected_task_key": entry["task_key"],
                     "observed_known_task_keys": other, "observed": observed}
            raise AcceptanceIdentityError("acceptance_identity_mismatch",
                                          "non-empty platform tests are wrong-family or unknown", audit)
        path = candidate.resolve()
        return AcceptanceSelection(path, _audit(entry, req_fp, task_input, "platform", path, observed))

    bundled = bundle_dir / "public-tests" / str(entry["suite_path"])
    observed = inspect_suite(bundled)
    if not _entry_matches_suite(entry, observed):
        audit = {"status": "acceptance_identity_invalid", "source": "bundled",
                 "task_key": entry["task_key"], "path": str(bundled), "observed": observed}
        raise AcceptanceIdentityError("acceptance_identity_invalid",
                                      "bundled tests failed manifest hash validation", audit)
    path = bundled.resolve()
    return AcceptanceSelection(path, _audit(entry, req_fp, task_input, "bundled", path, observed))
