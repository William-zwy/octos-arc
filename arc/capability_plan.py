"""Low-risk requirement-to-capability planning for isolated P0 experiments.

This module is intentionally additive: it does not replace the atomic-node
scheduler. Callers can inspect the plan or opt into the returned order.
"""
from __future__ import annotations

from collections import OrderedDict
from typing import Any, Iterable


CAPABILITY_ORDER = (
    "foundation",
    "resource_lifecycle",
    "core_mutation",
    "persistence",
    "secondary_actions",
    "advanced",
)

_KEYWORDS = OrderedDict(
    (
        ("foundation", ("entry", "route", "login", "session", "home", "list", "detail", "navigation", "grid", "editor")),
        ("resource_lifecycle", ("create", "open", "rename", "delete", "branch", "worksheet", "repository")),
        ("core_mutation", ("edit", "update", "cell", "issue", "pull request", "commit", "formula", "comment")),
        ("persistence", ("refresh", "reopen", "persist", "save", "restore", "reload")),
        ("secondary_actions", ("copy", "paste", "undo", "redo", "csv", "import", "export", "filter", "sort")),
        ("advanced", ("pivot", "validation", "permission", "merge", "review")),
    )
)


def _text(node: dict[str, Any]) -> str:
    fields = (node.get("name"), node.get("description"), node.get("capability"))
    contract = node.get("acceptance_contract") or {}
    fields += tuple(contract.get(key) for key in contract)
    return " ".join(str(value or "") for value in fields).lower()


def classify_node(node: dict[str, Any]) -> str:
    text = _text(node)
    for capability, keywords in _KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            return capability
    return "core_mutation"


def build_capability_plan(nodes: Iterable[dict[str, Any]]) -> dict[str, Any]:
    groups: OrderedDict[str, list[dict[str, Any]]] = OrderedDict(
        (name, []) for name in CAPABILITY_ORDER
    )
    for node in nodes:
        item = dict(node)
        item["capability"] = item.get("capability") or classify_node(item)
        groups.setdefault(item["capability"], []).append(item)
    return {
        "schema_version": 1,
        "mode": "shadow",
        "capabilities": [
            {"name": name, "node_ids": [str(node.get("id")) for node in groups[name]],
             "nodes": groups[name]}
            for name in CAPABILITY_ORDER if groups[name]
        ],
    }


def ordered_node_ids(plan: dict[str, Any]) -> list[str]:
    result: list[str] = []
    for capability in plan.get("capabilities", []):
        result.extend(str(node_id) for node_id in capability.get("node_ids", []))
    return result
