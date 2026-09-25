from __future__ import annotations

import argparse
from contextlib import ExitStack
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

import acceptance_identity
import main as m


def requirements(description: str, task_key: str | None = None) -> dict:
    root = {
        "id": "ROOT", "name": "BookStack Knowledge Base System", "type": "FOLDER",
        "description": description, "dependencies": [], "children": [{
            "id": "REQ-1", "name": "Open", "type": "ATOMIC", "description": "Open it",
            "dependencies": [], "scenarios": [{"name": "Open", "steps": [
                {"keyword": "WHEN", "content": "open"},
                {"keyword": "THEN", "content": "visible"},
            ]}],
        }],
    }
    if task_key:
        root["task_key"] = task_key
    return root


class _Events:
    def __init__(self):
        self.calls = []

    def __getattr__(self, name):
        def record(*args, **kwargs):
            self.calls.append((name, args, kwargs))
        return record


class _GenerationReached(RuntimeError):
    pass


class AcceptanceIdentityFlowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.bundle = self.root / "bundle"
        public = self.bundle / "public-tests"
        public.mkdir(parents=True)
        self.lite = requirements("Lite requirements", "arc-bench-lite--bookstack")
        self.web = requirements("Web requirements", "arc-bench-web--bookstack")
        self.entries = [self.add_suite("arc-bench-web--bookstack", self.web,
                                       "official-snapshot:20260918-000000Z"),
                        self.add_suite("arc-bench-lite--bookstack", self.lite,
                                       "official-snapshot:20260917-150121Z")]
        (public / "manifest.json").write_text(
            json.dumps({"schema_version": 2, "suites": self.entries}), encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def add_suite(self, task_key: str, tree: dict, snapshot: str) -> dict:
        suite = self.bundle / "public-tests" / task_key
        suite.mkdir()
        (suite / "REQ-1.spec.ts").write_text(f"// {task_key}\n", encoding="utf-8")
        (suite / "helpers.ts").write_text(f"// helper for {task_key}\n", encoding="utf-8")
        observed = acceptance_identity.inspect_suite(suite)
        return {
            "suite_path": task_key, "task_key": task_key,
            "competition": task_key.split("--", 1)[0], "snapshot": snapshot,
            "requirements_fingerprint": acceptance_identity.requirement_fingerprint(tree),
            **{key: observed[key] for key in ("spec_count", "specs_sha256", "helper_sha256")},
        }

    def run_flow(self, tree: dict, recorded_fingerprint: str | None = None, fail_persist: bool = False):
        req_dir = self.root / "tmp" / "arcbench" / "requirements-source"
        req_dir.mkdir(parents=True, exist_ok=True)
        (req_dir / "requirements.yaml").write_text(yaml.safe_dump(tree, allow_unicode=True), encoding="utf-8")
        output = self.root / "template"
        events = _Events()
        generation_calls = []

        class Runtime:
            def __init__(self):
                self.events = events
                self.traceability = type("Traceability", (), {
                    "store_requirement_tree": staticmethod(lambda _: None),
                })()

                class Git:
                    @staticmethod
                    def ensure_repo():
                        generation_calls.append("entered")
                        raise _GenerationReached("generation boundary")

                self.git = Git()

        runtime = Runtime()
        args = argparse.Namespace(web_port=3000, requirement_path_source="argv.requirement_path")
        flow = m.Flow(args, output, req_dir)
        log_lines = []
        patches = [
            patch.object(m, "BUNDLE_DIR", self.bundle),
            patch.object(m.AgentRuntime, "from_env", return_value=runtime),
            patch.object(m, "log", side_effect=log_lines.append),
            patch.object(m.Flow, "cleanup_playwright", return_value=None),
            patch.object(m.Flow, "stop_llm_proxy", return_value=None),
            patch.object(m, "_reap_stray_processes", return_value=None),
            patch.object(m, "_postflight_structure_check", return_value=None),
            patch.object(m, "_free_web_port", return_value=None),
            patch.dict(os.environ, {"ARCBENCH_TESTS_DIR": ""}),
        ]
        if recorded_fingerprint:
            patches.append(patch.object(acceptance_identity, "requirement_fingerprint",
                                        return_value=recorded_fingerprint))
        if fail_persist:
            patches.append(patch.object(m, "persist_acceptance_identity", side_effect=OSError("read-only output")))
        with ExitStack() as stack:
            for item in patches:
                stack.enter_context(item)
            result = flow.run()
        return result, output, events, generation_calls, log_lines

    def test_flow_success_persists_verified_lite_suite_before_generation(self):
        result, output, events, generation_calls, logs = self.run_flow(self.lite)
        audit = json.loads((output / ".arc" / "acceptance-suite-identity.json").read_text(encoding="utf-8"))
        self.assertEqual(result, 1)  # The test deliberately stops at the generation boundary.
        self.assertEqual(generation_calls, ["entered"])
        self.assertEqual(audit["task_key_source"], "requirements.task_key")
        self.assertEqual(audit["selected_suite"], "arc-bench-lite--bookstack")
        self.assertEqual(audit["manifest_entry_provenance"]["snapshot"], "official-snapshot:20260917-150121Z")
        self.assertEqual(audit["failure_classification"], None)
        self.assertTrue(any("acceptance identity" in line for line in logs))

    def test_flow_platform_shape_5dd_mismatch_writes_diagnostic_and_stops(self):
        tree = requirements("platform runtime tree")
        recorded = "5DD4F3C4226EE6E7426E9FF95526291F4663F2C1720BF411F33A0C8A54476F34"
        result, output, events, generation_calls, logs = self.run_flow(tree, recorded)
        audit = json.loads((output / ".arc" / "acceptance-suite-identity.json").read_text(encoding="utf-8"))
        self.assertEqual(result, 1)
        self.assertEqual(generation_calls, [])
        self.assertEqual(audit["failure_classification"], "identity_unverified")
        self.assertTrue(all(not item["present"] for item in audit["task_key_observations"]))
        self.assertEqual(audit["requirements_file_sha256"],
                         acceptance_identity._sha256(
                             self.root / "tmp" / "arcbench" / "requirements-source" / "requirements.yaml"))
        self.assertEqual(audit["canonical_tree_sha256"], recorded)
        self.assertIsNone(audit["selected_suite"])
        self.assertTrue(any("AcceptanceIdentityError('identity_unverified:" in line for line in logs))
        failed = [args[0] for name, args, _ in events.calls if name == "mark_run_failed"]
        self.assertTrue(failed and "identity_unverified" in failed[0])

    def test_identity_exception_is_preserved_if_audit_write_also_fails(self):
        tree = requirements("platform runtime tree")
        recorded = "5DD4F3C4226EE6E7426E9FF95526291F4663F2C1720BF411F33A0C8A54476F34"
        result, output, events, generation_calls, logs = self.run_flow(tree, recorded, fail_persist=True)
        self.assertEqual(result, 1)
        self.assertEqual(generation_calls, [])
        self.assertFalse((output / ".arc" / "acceptance-suite-identity.json").exists())
        self.assertTrue(any("diagnostic persistence failed (OSError)" in line for line in logs))
        self.assertTrue(any("AcceptanceIdentityError('identity_unverified:" in line for line in logs))
        failed = [args[0] for name, args, _ in events.calls if name == "mark_run_failed"]
        self.assertTrue(failed and "identity_unverified" in failed[0])


if __name__ == "__main__":
    unittest.main()
