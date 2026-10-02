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
    build_passed: bool,
    readiness_passed: bool,
    smoke_passed: bool,
    persistence_passed: bool,
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
    hard_failures = [name for name, ok in checks.items() if not ok]
    missing = [name for name in ("invariants", "capabilities", "nodes") if not contract.get(name)]
    score = sum(1 for ok in checks.values() if ok) * 20
    recommendations: list[str] = []
    if not source_changed:
        recommendations.append("stop: no product delta")
    if not readiness_passed:
        recommendations.append("repair canonical GET / and GET /api/health before feature work")
    if not smoke_passed:
        recommendations.append("run requirement-derived semantic smoke on the shared entry surface")
    if not persistence_passed:
        recommendations.append("verify refresh/reopen and failure atomicity on a disposable workspace")
    if missing:
        recommendations.append("compile requirements before implementation")
    status = "accepted" if not hard_failures and not missing and acceptance_known else "inconclusive"
    return {
        "schema_version": 1,
        "status": status,
        "score": score,
        "hard_failures": hard_failures,
        "missing_evidence": missing,
        "recommendations": recommendations,
        "checks": checks,
        "official_acceptance_unknown": not acceptance_known,
    }
