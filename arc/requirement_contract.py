"""Compile requirement YAML into a small, evidence-backed implementation contract.

The benchmark does not always provide acceptance specs.  In that mode the model
still needs exact actions, visible names, fixture values and persistence hints,
but replaying the complete YAML tree on every turn is expensive and ambiguous.
This module deliberately extracts facts without inventing domain-specific
routes or entities; every fact retains a source pointer and confidence.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any


ROLE_RE = re.compile(
    r"\b(button|link|textbox|heading|checkbox|radio|combobox|alert|tab|dialog|menu|row|gridcell|navigation)\b",
    re.I,
)
PATH_RE = re.compile(r"(?<![\w-])/(?:[A-Za-z0-9_:.?=&${}-]+(?:/[A-Za-z0-9_:.?=&${}-]+)*)")
QUOTED_RE = re.compile(r"(?:\"([^\"]+)\"|'([^']+)'|`([^`]+)`|“([^”]+)”|‘([^’]+)’)")
EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b")
SCOPE_RE = re.compile(
    r"\b(?:same|each|the selected|current|target|own|owned|parent|associated|corresponding|specific|independent)"
    r"[^.]{0,100}\b(?:record|item|entity|resource|question|issue|repository|branch|user|account|page|row|cell|tag|post)\b",
    re.I,
)
PERSIST_RE = re.compile(r"\b(reload|refresh|reopen|persist|persistent|saved|survive|database|store|after signing out|session)\b", re.I)
PERMISSION_RE = re.compile(r"\b(permission|permitted|authorized|privilege|role|logged in|signed in|anonymous|owner|moderator|access)\b", re.I)
GENERIC_EXACT_RE = re.compile(r"^(?:the|a|an|this|that|requested|workflow|item|record|thing|value|result|page|screen|feature|action|operation|data|user)$", re.I)
SURFACE_ROLE_RE = re.compile(
    r"\b(button|link|textbox|heading|checkbox|radio|combobox|alert|tab|dialog|menu|row|gridcell|navigation)\b",
    re.I,
)
SURFACE_ACTION_RE = re.compile(
    r"\b(click(?:s|ed|ing)?|open(?:s|ed|ing)?|select(?:s|ed|ing)?|navigate(?:s|d|ing)?|"
    r"switch(?:es|ed|ing)?|visit(?:s|ed|ing)?|go[- ]to|follow(?:s|ed|ing)?|"
    r"activate(?:s|d|ing)?|press(?:es|ed|ing)?|choose(?:s|n|ing)?)\b",
    re.I,
)
SURFACE_ROLE_WORDS = {
    "button", "link", "textbox", "heading", "checkbox", "radio", "combobox",
    "alert", "tab", "dialog", "menu", "row", "gridcell", "navigation",
}
SURFACE_FIXTURE_RE = re.compile(
    r"^(?:[-+]?\d+(?:\.\d+)?|[A-Z]{1,3}\d+(?::[A-Z]{1,3}\d+)?|"
    r"[^\s/]+(?:/[^\s/]+){1,})$",
    re.I,
)


def _usable_exact(value: str) -> bool:
    """Keep concrete quoted fixtures/labels out of generic prose."""
    value = _text(value)
    lowered = value.lower()
    return (bool(value) and len(value) <= 120
            and not GENERIC_EXACT_RE.fullmatch(value)
            and lowered not in {"the requested workflow", "the selected item", "the current page"})


def _text(value: Any) -> str:
    return " ".join(str(value or "").split())


def _surface_candidates(text: str, evidence: str | None = None) -> list[dict[str, str | None]]:
    """Extract likely public UI entries from action prose.

    Requirement fixtures contain usernames, emails, passwords, numbers and
    whole quoted sentences.  Only retain a quoted value when the surrounding
    sentence describes a UI action or explicitly associates it with a role.
    This keeps the shared smoke domain-neutral without treating every fixture
    as a page entry.
    """
    source = _text(text)
    if not SURFACE_ACTION_RE.search(source):
        return []
    values: list[tuple[str, int, int]] = []
    for match in QUOTED_RE.finditer(source):
        value = _text(next((part for part in match.groups() if part), ""))
        if (not value or not _usable_exact(value) or EMAIL_RE.fullmatch(value)
                or value.lower() in SURFACE_ROLE_WORDS or SURFACE_FIXTURE_RE.fullmatch(value)
                or value.startswith("/") or PATH_RE.fullmatch(value)
                or re.search(r"(?:password|passwd|secret|token|credential|email)", value, re.I)):
            continue
        if len(value) > 80:
            continue
        values.append((value, match.start(), match.end()))
    candidates: list[dict[str, str | None]] = []
    seen: set[tuple[str, str | None]] = set()
    for value, start, end in values:
        window_start = max(0, start - 72)
        window_end = min(len(source), end + 72)
        window = source[window_start:window_end]
        input_matches = list(re.finditer(
            r"\b(?:enter|fill|type|input|with|password|passwd|secret|token|credential|email|username|account)\b",
            window, re.I))
        action_matches = list(SURFACE_ACTION_RE.finditer(window))
        nearest_input = max((window_start + match.start() for match in input_matches if window_start + match.start() < start), default=-1)
        nearest_action = max((window_start + match.start() for match in action_matches if window_start + match.start() < start), default=-1)
        if nearest_input >= 0 and nearest_input > nearest_action:
            continue
        role = None
        role_matches = list(SURFACE_ROLE_RE.finditer(window))
        if role_matches:
            role_match = min(role_matches, key=lambda item: abs((window_start + item.start()) - start))
            if abs((window_start + role_match.start()) - start) <= 32:
                role = role_match.group(1).lower()
        key = (value, role)
        if key in seen:
            continue
        seen.add(key)
        candidates.append({"name": value, "role": role, "action": source[:360],
                           "source": source[:360], "evidence": evidence})
    return candidates


def _facts(text: str) -> dict[str, list[str]]:
    quoted: list[str] = []
    for match in QUOTED_RE.finditer(text):
        value = next((part for part in match.groups() if part), "").strip()
        if value and value not in quoted:
            quoted.append(value)
    for value in EMAIL_RE.findall(text):
        if value not in quoted:
            quoted.append(value)
    roles = sorted({match.group(1).lower() for match in ROLE_RE.finditer(text)})
    paths = list(dict.fromkeys(PATH_RE.findall(text)))
    scopes = list(dict.fromkeys(_text(match.group(0)) for match in SCOPE_RE.finditer(text)))
    usable_quoted = [value for value in quoted if _usable_exact(value)]
    return {
        "rejected_exact_values": [value for value in quoted if not _usable_exact(value)][:12],
        "exact_values": usable_quoted[:20],
        "roles": roles[:12],
        "paths": paths[:12],
        "scope_hints": scopes[:8],
        "persistence_hints": ["reload/reopen/session/persistence mentioned"] if PERSIST_RE.search(text) else [],
        "permission_hints": ["session/permission/access mentioned"] if PERMISSION_RE.search(text) else [],
    }


def _scenario_contract(node_id: str, scenario: dict, index: int) -> dict:
    name = _text(scenario.get("name") or "scenario")
    steps = [step for step in scenario.get("steps") or [] if isinstance(step, dict)]
    step_records: list[dict] = []
    all_text = " ".join([name] + [_text(step.get("content")) for step in steps])
    for step_index, step in enumerate(steps, 1):
        keyword = _text(step.get("keyword")).upper() or "STEP"
        content = _text(step.get("content"))
        if content:
            step_records.append({
                "keyword": keyword,
                "text": content[:360],
                "evidence": f"{node_id}:scenario[{index}]:step[{step_index}]",
            })
    facts = _facts(all_text)
    facts["actions"] = [step["text"] for step in step_records if step["keyword"] == "WHEN"][:6]
    facts["expected"] = [step["text"] for step in step_records if step["keyword"] == "THEN"][:6]
    facts["setup"] = [step["text"] for step in step_records if step["keyword"] == "GIVEN"][:6]
    return {
        "name": name[:180],
        "steps": step_records[:12],
        "facts": facts,
        "evidence": f"{node_id}:scenario[{index}]",
        "confidence": "high" if step_records else "medium",
    }


def compile_requirement_contract(tree: dict) -> dict:
    """Return a compact contract for all atomic nodes in document order."""
    nodes: list[dict] = []

    def walk(node: dict, parents: tuple[str, ...] = ()) -> None:
        node_id = _text(node.get("id"))
        node_type = _text(node.get("type")).upper()
        children = node.get("children") or []
        if node_id and (node_type != "FOLDER" and not children or node_type == "ATOMIC"):
            description = _text(node.get("description"))
            scenarios = [
                _scenario_contract(node_id, scenario, index)
                for index, scenario in enumerate(node.get("scenarios") or [], 1)
                if isinstance(scenario, dict)
            ]
            facts = _facts(" ".join([_text(node.get("name")), description]))
            nodes.append({
                "id": node_id,
                "name": _text(node.get("name"))[:180],
                "description": description[:420],
                "dependencies": [_text(dep) for dep in node.get("dependencies") or [] if _text(dep)],
                "parent_ids": list(parents),
                "scenario_count": len(scenarios),
                "facts": facts,
                "scenarios": scenarios,
                "evidence": f"{node_id}:description" if description else f"{node_id}:name",
                "confidence": "high" if scenarios else "medium",
            })
            return
        for child in children:
            if isinstance(child, dict):
                walk(child, parents + ((node_id,) if node_id else ()))

    walk(tree)
    capabilities_by_parent: dict[str, dict] = {}
    for item in nodes:
        # The first parent is normally the synthetic ROOT; use the first real
        # folder so the map groups an app into a small set of capabilities.
        parent_ids = item.get("parent_ids") or []
        parent_id = parent_ids[1] if len(parent_ids) > 1 else (parent_ids[0] if parent_ids else "ROOT")
        capability = capabilities_by_parent.setdefault(parent_id, {
            "id": parent_id,
            "node_ids": [],
            "node_names": [],
            "scenario_count": 0,
            "evidence": [],
            "confidence": "medium",
        })
        capability["node_ids"].append(item["id"])
        capability["node_names"].append(item.get("name") or item["id"])
        capability["scenario_count"] += item.get("scenario_count", 0)
        capability["evidence"].append(item.get("evidence"))

    invariants: list[dict] = []
    seen_invariants: set[str] = set()
    for item in nodes:
        for scenario in item.get("scenarios") or []:
            facts = scenario.get("facts") or {}
            expected = facts.get("expected") or []
            combined = " ".join(expected + facts.get("setup", []) + facts.get("actions", []))
            checks: list[tuple[str, str]] = []
            if re.search(r"\b(refresh|reload|reopen|survive|persist|saved)\b", combined, re.I):
                checks.append(("refresh_reopen", combined[:360]))
            if re.search(r"\b(atomic|partial|rollback|unchanged|not create|no .*created|failure)\b", combined, re.I):
                checks.append(("failure_atomicity", combined[:360]))
            if re.search(r"\b(initial|seed|existing|starting state|pre-populated|verified account)\b", combined, re.I):
                checks.append(("initial_seed", combined[:360]))
            for kind, quote in checks:
                key = f"{kind}:{quote.lower()}"
                if key in seen_invariants:
                    continue
                seen_invariants.add(key)
                invariants.append({"kind": kind, "quote": quote,
                                   "evidence": scenario.get("evidence"), "confidence": "high"})

    for item in nodes:
        scenarios = item.get("scenarios") or []
        exact_values: list[str] = []
        routes: list[str] = []
        roles: list[str] = []
        actions: list[str] = []
        visible: list[str] = []
        errors: list[str] = []
        refresh: list[str] = []
        evidence: list[str] = []
        for scenario in scenarios:
            facts = scenario.get("facts") or {}
            for key, target in (("exact_values", exact_values), ("paths", routes), ("roles", roles),
                                ("actions", actions), ("expected", visible)):
                for value in facts.get(key) or []:
                    if value not in target:
                        target.append(value)
            expected = facts.get("expected") or []
            for value in expected:
                if re.search(r"\b(error|invalid|fail|cannot|empty|not found|denied|reject)\b", value, re.I):
                    errors.append(value)
                if re.search(r"\b(refresh|reload|reopen|persist|survive|saved)\b", value, re.I):
                    refresh.append(value)
            if scenario.get("evidence"):
                evidence.append(scenario["evidence"])
        item["acceptance_contract"] = {
            "fixture": exact_values[:20],
            "entry_route": routes[:12],
            "role_name": roles[:12] + [value for value in exact_values if value not in roles][:12],
            "user_action": actions[:12],
            "api_mutation": [path for path in routes if "/api" in path][:12],
            "visible_result": visible[:12],
            "error_behavior": errors[:12],
            "refresh_reopen_result": refresh[:12],
            "evidence": evidence[:12],
            "confidence": "high" if scenarios else "medium",
        }
    payload = {
        "schema_version": 1,
        "source": "requirements.yaml",
        "root": {"id": _text(tree.get("id")), "name": _text(tree.get("name")),
                 "description": _text(tree.get("description"))[:420]},
        "atomic_count": len(nodes),
        "scenario_count": sum(item["scenario_count"] for item in nodes),
        "nodes": nodes,
        "capabilities": list(capabilities_by_parent.values()),
        "invariants": invariants[:80],
    }
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    payload["contract_hash"] = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
    return payload



def compile_requirement_compilation(tree: dict) -> dict:
    """Compile a bounded, evidence-backed first pass before implementation."""
    contract = compile_requirement_contract(tree)
    vague_re = re.compile(r"\b(fast|quickly|quick|support|easy|simple|seamless|etc\.)\b", re.I)
    implicit = [
        {"kind": "health", "requirement": "canonical start serves /health and /api/health", "confidence": "derived"},
        {"kind": "static", "requirement": "root and static assets remain reachable", "confidence": "derived"},
        {"kind": "404", "requirement": "unknown routes return a controlled response without process exit", "confidence": "derived"},
        {"kind": "transport", "requirement": "same-origin API, encoding and JSON error responses are stable", "confidence": "derived"},
    ]
    questions = []
    traceability = []
    for node in contract.get("nodes", []):
        description = str(node.get("description") or "")
        if vague_re.search(description):
            questions.append({"node_id": node.get("id"), "text": description[:360], "assumption": "choose the smallest deterministic behavior that satisfies explicit examples", "confidence": "assumed", "evidence": node.get("evidence")})
        scenarios = node.get("scenarios") or []
        gwt = []
        examples = []
        boundaries = [
            {"case": "empty input", "expected": "controlled validation error; no partial mutation", "confidence": "derived"},
            {"case": "invalid input", "expected": "4xx or visible error; state unchanged", "confidence": "derived"},
            {"case": "duplicate submission", "expected": "idempotent or explicit conflict; no duplicate entity", "confidence": "derived"},
        ]
        for scenario in scenarios[:8]:
            facts = scenario.get("facts") or {}
            setup = facts.get("setup") or ["Given the fixture described by the requirement"]
            actions = facts.get("actions") or ["When the user performs the named action"]
            expected = facts.get("expected") or ["Then the visible result matches the requirement"]
            gwt.append({"given": setup[:3], "when": actions[:3], "then": expected[:3], "evidence": scenario.get("evidence"), "confidence": scenario.get("confidence", "derived")})
            examples.append({"input": setup[:2] + actions[:1], "output": expected[:2], "confidence": "explicit" if scenario.get("steps") else "derived", "evidence": scenario.get("evidence")})
        if len(examples) == 1:
            examples.append({"input": ["Repeat the action after refresh/reopen"], "output": ["The persisted visible result remains stable"], "confidence": "derived", "evidence": node.get("evidence")})
        node["first_pass_compilation"] = {"given_when_then": gwt[:8], "examples": examples[:2], "boundaries": boundaries, "source_refs": [node.get("evidence")] + [item.get("evidence") for item in gwt[:7] if item.get("evidence")], "confidence": "explicit" if scenarios else "derived"}
        traceability.append({"requirement": node.get("evidence"), "node_id": node.get("id"), "plan_path": f"capabilities/{node.get('id')}", "smoke_case": f"requirements-derived/{node.get('id')}", "confidence": node.get("confidence", "derived")})
    contract["implicit_requirements"] = implicit
    contract["clarification_questions"] = questions[:40]
    contract["traceability"] = traceability
    contract["compilation_phase"] = {"write_code": False, "source": "requirements.yaml", "bounded": True}
    return contract

def compact_contract(contract: dict, node_id: str | None = None, max_chars: int = 7000) -> str:
    """Serialize either one node or a bounded summary for a prompt."""
    nodes = contract.get("nodes") or []
    if node_id:
        selected = [node for node in nodes if str(node.get("id")) == str(node_id)]
        payload = {
            "schema_version": contract.get("schema_version", 1),
            "contract_hash": contract.get("contract_hash"),
            "node": selected[0] if selected else {"id": node_id, "confidence": "low", "evidence": "not found"},
        }
    else:
        fixture_catalog: list[str] = []
        for node in nodes:
            for value in (node.get("facts") or {}).get("exact_values") or []:
                if value not in fixture_catalog and len(value) <= 100:
                    fixture_catalog.append(value)
        signals = []
        for node in nodes:
            facts = node.get("facts") or {}
            flags = [key for key in ("roles", "paths", "scope_hints", "persistence_hints", "permission_hints")
                     if facts.get(key)]
            signals.append({"id": node.get("id"), "flags": flags})
        payload = {
            "schema_version": contract.get("schema_version", 1),
            "contract_hash": contract.get("contract_hash"),
            "atomic_count": contract.get("atomic_count", 0),
            "scenario_count": contract.get("scenario_count", 0),
            "fixture_catalog": fixture_catalog[:40],
            "capabilities": [{"id": item.get("id"), "node_ids": item.get("node_ids"),
                              "scenario_count": item.get("scenario_count"),
                              "evidence": (item.get("evidence") or [])[:4]}
                             for item in contract.get("capabilities") or []],
            "invariants": [{"kind": item.get("kind"), "quote": str(item.get("quote") or "")[:200],
                            "evidence": item.get("evidence")}
                           for item in (contract.get("invariants") or [])[:20]],
            "nodes": [
                {"id": node.get("id"), "name": node.get("name"), "dependencies": node.get("dependencies"),
                 "scenario_count": node.get("scenario_count"), "confidence": node.get("confidence")}
                for node in nodes
            ],
            "signals": signals,
        }
    text = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    if len(text) <= max_chars:
        return text
    if node_id and isinstance(payload.get("node"), dict):
        node = payload["node"]
        node["scenarios"] = node.get("scenarios", [])[:2]
        node["description"] = str(node.get("description") or "")[:240]
        for facts in (node.get("facts"),):
            if isinstance(facts, dict):
                facts["exact_values"] = facts.get("exact_values", [])[:10]
                facts["scope_hints"] = facts.get("scope_hints", [])[:4]
        node["steps"] = node.get("steps", [])[:4]
        if isinstance(node.get("acceptance_contract"), dict):
            node["acceptance_contract"] = {
                key: list(value)[:4] if isinstance(value, list) else value
                for key, value in node["acceptance_contract"].items()
            }
        text = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    if len(text) > max_chars:
        # Keep the result valid JSON even when a requirement contains long prose.
        node = payload.get("node")
        if isinstance(node, dict):
            node["scenarios"] = []
            node["description"] = str(node.get("description") or "")[:120]
            node["facts"] = {"exact_values": [], "roles": [], "paths": [], "scope_hints": [],
                              "persistence_hints": [], "permission_hints": []}
        if not node_id:
            payload["fixture_catalog"] = list(payload.get("fixture_catalog") or [])[:20]
            payload["nodes"] = [{"id": item.get("id"), "name": item.get("name"),
                                 "scenario_count": item.get("scenario_count"),
                                 "dependencies": item.get("dependencies") or []}
                                for item in nodes]
            payload["capabilities"] = [{"id": item.get("id"), "node_ids": item.get("node_ids") or [],
                                         "scenario_count": item.get("scenario_count")}
                                        for item in contract.get("capabilities") or []]
            payload["invariants"] = [{"kind": item.get("kind"), "evidence": item.get("evidence")}
                                     for item in (contract.get("invariants") or [])[:20]]
            payload["signals"] = [{"id": item.get("id"), "flags": item.get("flags") or []}
                                  for item in payload.get("signals") or [] if item.get("flags")]
            text = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        payload["truncated"] = True
        text = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    return text if len(text) <= max_chars else json.dumps({"schema_version": 1, "truncated": True,
                                                            "node_id": node_id, "contract_hash": contract.get("contract_hash")},
                                                           ensure_ascii=False, separators=(",", ":"))


def requirement_smoke_gate(contract: dict, node_id: str | None = None) -> dict:
    """Build a minimal evidence checklist for a requirement-only smoke run."""
    nodes = contract.get("nodes") or []
    node = next((item for item in nodes if str(item.get("id")) == str(node_id)), None) if node_id else None
    source = (node or {}).get("acceptance_contract") or {}
    keys = ("entry_route", "role_name", "user_action", "api_mutation", "visible_result",
            "error_behavior", "refresh_reopen_result")
    required = [key for key in keys if source.get(key)]
    return {"status": "pending", "node_id": node_id,
            "contract_hash": contract.get("contract_hash"), "required": required,
            "evidence": {key: False for key in required}}


def evaluate_requirement_smoke_gate(gate: dict, evidence: dict | None) -> dict:
    """Evaluate explicit smoke evidence; malformed input is inconclusive."""
    required = gate.get("required") if isinstance(gate, dict) else None
    if not isinstance(required, list) or not isinstance(evidence, dict):
        return {**(gate if isinstance(gate, dict) else {}), "status": "inconclusive",
                "reason": "missing_evidence"}
    observed = {key: bool(evidence.get(key)) for key in required}
    return {**gate, "status": "passed" if all(observed.values()) else "failed",
            "evidence": observed,
            "missing": [key for key, value in observed.items() if not value]}




def shared_surface_contract(contract: dict) -> dict:
    """Derive a bounded family of public-entry probes from requirements.

    The compiler has no domain vocabulary.  It therefore carries the first
    role candidates and exact names found in the requirement evidence, along
    with the first action/result hints.  The runtime can use this structure for
    a browser smoke without embedding strings from a particular benchmark.
    """
    routes: list[str] = []; labels: list[str] = []; roles: list[str] = []; actions: list[str] = []
    visible: list[str] = []; entries: list[dict] = []; fanout: dict[str, int] = {}
    candidate_by_key: dict[tuple[str, str | None], dict] = {}
    candidate_order: list[tuple[str, str | None]] = []
    for node in contract.get("nodes") or []:
        c = node.get("acceptance_contract") or {}
        for value in c.get("entry_route") or []:
            if str(value).startswith("/") and value not in routes: routes.append(str(value))
        for value in c.get("user_action") or []:
            if value and value not in actions: actions.append(str(value))
        for value in c.get("visible_result") or []:
            value = _text(value)
            if _usable_exact(value) and value not in visible:
                visible.append(value)
        node_candidate_count = 0
        for scenario in node.get("scenarios") or []:
            for step in scenario.get("steps") or []:
                text = str(step.get("text") or "")
                if not text or str(step.get("keyword") or "").upper() != "WHEN":
                    continue
                for candidate in _surface_candidates(text, step.get("evidence") or scenario.get("evidence")):
                    key = (str(candidate["name"]), candidate.get("role"))
                    if key not in candidate_by_key:
                        candidate_by_key[key] = candidate
                        candidate_order.append(key)
                    node_candidate_count += 1
                    fanout[str(candidate["name"])] = fanout.get(str(candidate["name"]), 0) + 1
        # Do not fall back to role_name: it intentionally combines roles and
        # fixtures, so it cannot distinguish a public entry from seed data.
        if node_candidate_count == 0:
            continue
    # High-fanout entries are the best shared-surface probes.  Keep source
    # order as the tie breaker so the first public workflow remains visible.
    ui_route = next((route for route in routes if not route.startswith("/api/")), "/")
    ranked = sorted(candidate_order, key=lambda key: (-fanout.get(key[0], 0),
                                                       0 if key[1] in {"button", "link", "tab", "heading"} else 1,
                                                       candidate_order.index(key)))[:8]
    for key in ranked:
        candidate = candidate_by_key[key]
        labels.append(str(candidate["name"]))
        if candidate.get("role") and candidate["role"] not in roles:
            roles.append(str(candidate["role"]))
        entries.append({
            "name": candidate["name"], "role": candidate.get("role"),
            "route": ui_route, "action": candidate.get("action") or (actions[0] if actions else None),
            "expected": visible[:3], "evidence": candidate.get("evidence"),
            "source": candidate.get("source"),
        })
    return {"route": ui_route, "role": roles[0] if roles else None,
            "name": labels[0] if labels else None, "names": labels,
            "action": actions[0] if actions else None, "expected": visible[:8],
            "entries": entries, "fanout": fanout,
            "confidence": "high" if labels else "unknown"}
