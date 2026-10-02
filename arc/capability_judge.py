"""Deterministic capability scorecard for requirement-only runs.

This is deliberately a shadow judge: it summarizes evidence for the model and
checkpoint, but cannot mark a node implemented or replace acceptance.py.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any


@dataclass(frozen=True)
class JudgeResult:
    status: str
    score: int
    hard_failures: list[str]
    missing_evidence: list[str]
    recommendations: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def judge_round(
    contract: dict[str, Any],
    *,
    source_changed: bool,
    build_passed: bool | None,
    readiness_passed: bool | None,
    smoke_passed: bool | None,
    persistence_passed: bool | None,
    acceptance_known: bool = False,
) -> dict[str, Any]:
    """Return a conservative, evidence-only scorecard.

    The result is intentionally fail-closed: ``verified`` is never emitted and
    ``status=accepted`` is impossible without all local evidence plus a known
    acceptance result.  This prevents the analyst skill from becoming a second,
    model-controlled completion mechanism.
    """
    checks = {
        "source_changed": source_changed,
        "build": build_passed,
        "readiness": readiness_passed,
        "semantic_smoke": smoke_passed,
        "persistence": persistence_passed,
    }
    hard_failures = [name for name, ok in checks.items() if ok is False]
    unknown = [name for name, ok in checks.items() if ok is None]
    missing = [name for name in ("invariants", "capabilities", "nodes") if not contract.get(name)]
    score = sum(1 for ok in checks.values() if ok) * 20
    recommendations: list[str] = []
    if not source_changed:
        recommendations.append("stop: no product delta")
    if readiness_passed is not True:
        recommendations.append("repair canonical GET / and GET /api/health before feature work")
    if smoke_passed is not True:
        recommendations.append("run requirement-derived semantic smoke on the shared entry surface")
    if persistence_passed is not True:
        recommendations.append("verify refresh/reopen and failure atomicity on a disposable workspace")
    if missing:
        recommendations.append("compile requirements before implementation")
    all_required_passed = all(ok is True for ok in checks.values())
    status = "accepted" if all_required_passed and not missing and acceptance_known else "inconclusive"
    return {
        "schema_version": 1,
        "status": status,
        "score": score,
        "hard_failures": hard_failures,
        "unknown_evidence": unknown,
        "missing_evidence": missing,
        "recommendations": recommendations,
        "checks": checks,
        "official_acceptance_unknown": not acceptance_known,
        "smoke_plan": contract_smoke_plan(contract),
    }

def contract_smoke_plan(contract: dict[str, Any], node_id: str | None = None) -> dict[str, Any]:
    """Derive a bounded semantic smoke checklist from the compiled contract."""
    nodes = contract.get("nodes") or []
    node = next((item for item in nodes if str(item.get("id")) == str(node_id)), None) if node_id else None
    contract_item = (node or {}).get("acceptance_contract") or {}
    checks = []
    for key, label in (("entry_route", "route"), ("role_name", "accessible_name"),
                       ("user_action", "action"), ("api_mutation", "mutation"),
                       ("visible_result", "visible_result"), ("error_behavior", "error_atomicity"),
                       ("refresh_reopen_result", "refresh_reopen")):
        if contract_item.get(key):
            checks.append({"kind": label, "source": key, "required": True})
    return {"schema_version": 1, "node_id": node_id, "checks": checks,
            "contract_hash": contract.get("contract_hash")}
