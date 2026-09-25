"""Fail-closed identity routing for bundled ARC acceptance suites."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


IDENTITY_MANIFEST = "manifest.json"
TASK_KEY_PRIORITY = ("requirements.task_key", "requirements.taskKey", "requirement_path_component")
_FINGERPRINT_RE = re.compile(r"^[0-9A-Fa-f]{64}$")
_COMMIT_RE = re.compile(r"^[0-9A-Fa-f]{40}$")


def _has_snapshot_provenance(value: str) -> bool:
    if value.startswith("official-snapshot:"):
        return re.fullmatch(r"official-snapshot:\d{8}-\d{6}Z", value) is not None
    if value.startswith("repository:"):
        return _COMMIT_RE.fullmatch(value.partition(":")[2]) is not None
    return False


class AcceptanceIdentityError(RuntimeError):
    """Acceptance tests could not be tied to exactly one trusted task identity."""

    def __init__(self, status: str, detail: str, audit: dict | None = None):
        super().__init__(f"{status}: {detail}")
        self.status = status
        self.audit = audit or {"status": status, "failure_classification": status, "detail": detail}


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


def _requirements_file(req_dir: Path) -> Path | None:
    for name in ("requirements.yaml", "requirements.yml"):
        path = req_dir / name
        if path.is_file():
            return path
    return None


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


def _load_manifest(bundle_dir: Path) -> tuple[list[dict], str]:
    path = bundle_dir / "public-tests" / IDENTITY_MANIFEST
    try:
        raw_bytes = path.read_bytes()
        raw = json.loads(raw_bytes.decode("utf-8"))
    except Exception as exc:  # noqa: BLE001
        audit = {"status": "identity_manifest_invalid", "failure_classification": "identity_manifest_invalid",
                 "manifest_path": str(path), "manifest_sha256": None}
        raise AcceptanceIdentityError("identity_manifest_invalid", f"manifest unreadable: {exc}", audit) from exc
    manifest_sha256 = hashlib.sha256(raw_bytes).hexdigest().upper()
    if not isinstance(raw, dict) or raw.get("schema_version") != 2 or not isinstance(raw.get("suites"), list):
        audit = {"status": "identity_manifest_invalid", "failure_classification": "identity_manifest_invalid",
                 "manifest_path": str(path), "manifest_sha256": manifest_sha256}
        raise AcceptanceIdentityError("identity_manifest_invalid", "manifest schema must be version 2", audit)
    required = {"suite_path", "task_key", "competition", "snapshot", "requirements_fingerprint",
                "spec_count", "specs_sha256", "helper_sha256"}
    suites = raw["suites"]
    valid = all(
        isinstance(item, dict)
        and required.issubset(item)
        and all(isinstance(item[field], str) and item[field].strip()
                for field in ("suite_path", "task_key", "competition", "snapshot"))
        and _has_snapshot_provenance(item["snapshot"])
        and isinstance(item["requirements_fingerprint"], str)
        and _FINGERPRINT_RE.fullmatch(item["requirements_fingerprint"]) is not None
        and type(item["spec_count"]) is int and item["spec_count"] >= 0
        and isinstance(item["specs_sha256"], str)
        and _FINGERPRINT_RE.fullmatch(item["specs_sha256"]) is not None
        and (item["helper_sha256"] is None or
             (isinstance(item["helper_sha256"], str) and _FINGERPRINT_RE.fullmatch(item["helper_sha256"]) is not None))
        for item in suites
    )
    if not valid:
        audit = {"status": "identity_manifest_invalid", "failure_classification": "identity_manifest_invalid",
                 "manifest_path": str(path), "manifest_sha256": manifest_sha256}
        raise AcceptanceIdentityError("identity_manifest_invalid", "suite entry or snapshot provenance is incomplete",
                                      audit)
    keys = [item["task_key"] for item in suites]
    if len(keys) != len(set(keys)):
        audit = {"status": "identity_manifest_ambiguous", "failure_classification": "identity_manifest_ambiguous",
                 "manifest_path": str(path), "manifest_sha256": manifest_sha256,
                 "duplicate_task_keys": sorted({key for key in keys if keys.count(key) > 1}),
                 "manifest_entries_considered": [
                     {"task_key": item["task_key"], "suite_path": item["suite_path"],
                      "snapshot": item["snapshot"], "requirements_fingerprint": item["requirements_fingerprint"]}
                     for item in suites
                 ]}
        raise AcceptanceIdentityError("identity_manifest_ambiguous",
                                      "schema v2 permits one fingerprint/snapshot per task key", audit)
    return suites, manifest_sha256


def _task_key_observations(tree: dict, req_dir: Path, known_keys: set[str]) -> list[dict]:
    observations = []
    for field in ("task_key", "taskKey"):
        present = field in tree
        value = tree.get(field)
        observations.append({"source": f"requirements.{field}", "present": present,
                             "value": value if isinstance(value, str) else None,
                             "trusted_shape": not present or (isinstance(value, str) and bool(value.strip()))})
    matching_parts = [part for part in reversed(req_dir.resolve().parts) if part in known_keys]
    if matching_parts:
        observations.extend({"source": "requirement_path_component", "present": True,
                             "value": part, "trusted_shape": True} for part in matching_parts)
    else:
        observations.append({"source": "requirement_path_component", "present": False,
                             "value": None, "trusted_shape": True})
    return observations


def _base_audit(tree: dict, req_dir: Path, bundle_dir: Path, manifest_sha256: str,
                requirement_path_source: str, suites: list[dict]) -> dict:
    req_file = _requirements_file(req_dir)
    req_file_sha256 = _sha256(req_file) if req_file else None
    req_fp = requirement_fingerprint(tree)
    return {
        "status": None,
        "failure_classification": None,
        "identity_input_priority": list(TASK_KEY_PRIORITY),
        "requirement_path_source": requirement_path_source,
        "requirement_path_component": req_dir.name,
        "task_key_source": None,
        "task_key_input": None,
        "task_key": None,
        "task_key_observations": [],
        "task_snapshot_source": "unavailable",
        "task_snapshot_input": None,
        "requirements_file": req_file.name if req_file else None,
        "requirements_file_sha256": req_file_sha256,
        "canonical_tree_sha256": req_fp,
        "requirements_fingerprint": req_fp,
        "manifest_path": str(bundle_dir / "public-tests" / IDENTITY_MANIFEST),
        "manifest_sha256": manifest_sha256,
        "manifest_entries_considered": [
            {"task_key": item["task_key"], "suite_path": item["suite_path"],
             "snapshot": item["snapshot"], "requirements_fingerprint": item["requirements_fingerprint"]}
            for item in suites
        ],
        "manifest_entry": None,
        "manifest_entry_provenance": None,
        "selected_suite": None,
        "selected_path": None,
        "matching_suites": [],
    }


def _fail(status: str, detail: str, audit: dict) -> None:
    audit["status"] = status
    audit["failure_classification"] = status
    raise AcceptanceIdentityError(status, detail, audit)


def _entry_audit(audit: dict, entry: dict) -> None:
    audit["manifest_entry"] = dict(entry)
    audit["manifest_entry_provenance"] = {
        "snapshot": entry["snapshot"],
        "manifest_sha256": audit["manifest_sha256"],
    }
    audit["task_snapshot_source"] = "manifest_entry.snapshot"
    audit["task_snapshot_input"] = entry["snapshot"]
    audit["task_key"] = entry["task_key"]


def _entry_matches_suite(entry: dict, observed: dict) -> bool:
    return all(observed.get(field) == entry.get(field)
               for field in ("spec_count", "specs_sha256", "helper_sha256"))


def _audit(audit: dict, selection_basis: str, suite_source: str,
           path: Path, observed: dict) -> dict:
    return {
        **audit,
        "status": "selected",
        "failure_classification": None,
        "selection_basis": selection_basis,
        "selected_suite": audit["manifest_entry"]["suite_path"],
        "selected_path": str(path.resolve()),
        "suite_source": suite_source,
        "helper_sha256": observed["helper_sha256"],
        "specs_sha256": observed["specs_sha256"],
        "spec_count": observed["spec_count"],
        "spec_files": observed["spec_files"],
    }


def locate_acceptance_suite(tree: dict, req_dir: Path, bundle_dir: Path,
                            platform_candidates: list[Path], logger: Callable[[str], None],
                            requirement_path_source: str = "function_argument") -> AcceptanceSelection:
    try:
        suites, manifest_sha256 = _load_manifest(bundle_dir)
    except AcceptanceIdentityError as exc:
        diagnostic = _base_audit(tree, req_dir, bundle_dir, exc.audit.get("manifest_sha256"),
                                  requirement_path_source, [])
        diagnostic["task_key_observations"] = _task_key_observations(tree, req_dir, set())
        diagnostic.update(exc.audit)
        diagnostic["status"] = exc.status
        diagnostic["failure_classification"] = exc.status
        detail = str(exc).partition(": ")[2] or str(exc)
        raise AcceptanceIdentityError(exc.status, detail, diagnostic) from exc
    known = {item["task_key"] for item in suites}
    req_fp = requirement_fingerprint(tree)
    audit = _base_audit(tree, req_dir, bundle_dir, manifest_sha256, requirement_path_source, suites)
    if audit["requirements_file_sha256"] is None:
        _fail("identity_unverified", "requirements source file is missing", audit)

    observations = _task_key_observations(tree, req_dir, known)
    audit["task_key_observations"] = observations
    supplied = [item for item in observations if item["present"]]
    invalid = [item for item in supplied if not item["trusted_shape"]]
    if invalid:
        _fail("identity_unverified", "task key metadata has an invalid shape", audit)
    values = {item["value"] for item in supplied}
    if len(values) > 1:
        _fail("identity_conflict", "task key sources disagree", audit)
    if supplied:
        selected_input = supplied[0]
        task_key = selected_input["value"]
        audit["task_key_source"] = selected_input["source"]
        audit["task_key_input"] = task_key
        if task_key not in known:
            _fail("identity_unverified", "explicit task key is not registered in the manifest", audit)
        matches = [item for item in suites if item["task_key"] == task_key]
        if len(matches) != 1:
            _fail("identity_ambiguous", f"expected one manifest entry for task key, found {len(matches)}", audit)
        entry = matches[0]
        _entry_audit(audit, entry)
        audit["matching_suites"] = [entry["suite_path"]]
        if entry["requirements_fingerprint"].upper() != req_fp:
            audit["expected_fingerprint"] = entry["requirements_fingerprint"].upper()
            _fail("identity_snapshot_mismatch", "explicit task key does not match its registered snapshot", audit)
        match_source = "task_key"
    else:
        matches = [item for item in suites if item["requirements_fingerprint"].upper() == req_fp]
        audit["matching_suites"] = [item["suite_path"] for item in matches]
        if len(matches) != 1:
            status = "identity_ambiguous" if len(matches) > 1 else "identity_unverified"
            _fail(status, f"expected one provenance-backed exact fingerprint, found {len(matches)}", audit)
        entry = matches[0]
        _entry_audit(audit, entry)
        match_source = "requirements_fingerprint"

    for candidate in platform_candidates:
        observed = inspect_suite(candidate)
        if not observed["spec_count"]:
            logger(f"[tests] platform candidate {candidate}: no *.spec.ts")
            continue
        if not _entry_matches_suite(entry, observed):
            other = [item["task_key"] for item in suites if _entry_matches_suite(item, observed)]
            failure = dict(audit)
            failure.update({"status": "identity_suite_mismatch", "failure_classification": "identity_suite_mismatch",
                            "suite_candidate": str(candidate), "expected_task_key": entry["task_key"],
                            "observed_known_task_keys": other, "observed_suite": observed})
            raise AcceptanceIdentityError("identity_suite_mismatch",
                                          "non-empty platform tests are wrong-family or unknown", failure)
        path = candidate.resolve()
        return AcceptanceSelection(path, _audit(audit, match_source, "platform", path, observed))

    bundled = bundle_dir / "public-tests" / entry["suite_path"]
    observed = inspect_suite(bundled)
    if not _entry_matches_suite(entry, observed):
        failure = dict(audit)
        failure.update({"status": "identity_bundle_invalid", "failure_classification": "identity_bundle_invalid",
                        "selected_path": str(bundled), "observed_suite": observed})
        raise AcceptanceIdentityError("identity_bundle_invalid",
                                      "bundled tests failed manifest hash validation", failure)
    path = bundled.resolve()
    return AcceptanceSelection(path, _audit(audit, match_source, "bundled", path, observed))
