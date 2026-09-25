from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

from acceptance_identity import (AcceptanceIdentityError, inspect_suite,
                                 locate_acceptance_suite, requirement_fingerprint)


def tree(description: str, child_description: str = "atomic") -> dict:
    return {
        "id": "ROOT", "name": "BookStack Knowledge Base System", "type": "FOLDER",
        "description": description, "dependencies": [], "children": [{
            "id": "REQ-1", "name": "Open", "type": "ATOMIC",
            "description": child_description, "dependencies": [],
            "scenarios": [{"name": "Open", "steps": [
                {"keyword": "WHEN", "content": "the user opens it"},
                {"keyword": "THEN", "content": "it is visible"},
            ]}],
        }],
    }


class AcceptanceIdentityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.bundle = self.root / "bundle"
        (self.bundle / "public-tests").mkdir(parents=True)
        self.logs = []

    def tearDown(self):
        self.temp.cleanup()

    def add_suite(self, task_key: str, requirement_tree: dict, spec_text: str,
                  snapshot: str = "official-snapshot:20260918-000000Z") -> dict:
        suite = self.bundle / "public-tests" / task_key
        suite.mkdir()
        (suite / "REQ-1.spec.ts").write_text(spec_text, encoding="utf-8")
        (suite / "helpers.ts").write_text(f"// {task_key}", encoding="utf-8")
        observed = inspect_suite(suite)
        return {
            "suite_path": task_key, "task_key": task_key,
            "competition": task_key.split("--", 1)[0], "snapshot": snapshot,
            "requirements_fingerprint": requirement_fingerprint(requirement_tree),
            "spec_count": observed["spec_count"], "specs_sha256": observed["specs_sha256"],
            "helper_sha256": observed["helper_sha256"],
        }

    def write_manifest(self, entries: list[dict]) -> None:
        (self.bundle / "public-tests" / "manifest.json").write_text(
            json.dumps({"schema_version": 2, "suites": entries}), encoding="utf-8")

    def locate(self, requirement_tree: dict, candidates: list[Path] | None = None):
        req = self.root / "tmp" / "arcbench" / "requirements-source"
        req.mkdir(parents=True, exist_ok=True)
        (req / "requirements.yaml").write_text(yaml.safe_dump(requirement_tree, allow_unicode=True),
                                               encoding="utf-8")
        return locate_acceptance_suite(requirement_tree, req, self.bundle, candidates or [], self.logs.append,
                                       requirement_path_source="argv.requirement_path")

    def test_same_root_title_routes_only_by_exact_fingerprint(self):
        web, lite = tree("web description"), tree("lite description")
        entries = [self.add_suite("arc-bench-web--bookstack", web, "// web"),
                   self.add_suite("arc-bench-lite--bookstack", lite, "// lite")]
        self.write_manifest(entries)
        web_selection = self.locate(web)
        self.assertIsNone(web_selection.audit["task_key_input"])
        self.assertEqual(web_selection.audit["selected_suite"], "arc-bench-web--bookstack")
        lite_selection = self.locate(lite)
        self.assertIsNone(lite_selection.audit["task_key_input"])
        self.assertEqual(lite_selection.audit["selected_suite"], "arc-bench-lite--bookstack")
        self.assertEqual(lite_selection.audit["task_snapshot_source"], "manifest_entry.snapshot")
        self.assertNotIn("arc-bench-web--bookstack", str(lite_selection.path))

    def test_title_only_identity_fails_closed_with_source_diagnostics(self):
        web = tree("web description")
        self.write_manifest([self.add_suite("arc-bench-web--bookstack", web, "// web"),
                             self.add_suite("arc-bench-lite--bookstack", tree("lite"), "// lite")])
        with self.assertRaises(AcceptanceIdentityError) as raised:
            self.locate({"id": "ROOT", "name": web["name"], "type": "FOLDER"})
        self.assertEqual(raised.exception.status, "identity_unverified")
        self.assertEqual(raised.exception.audit["task_key_source"], None)
        self.assertIsNotNone(raised.exception.audit["requirements_file_sha256"])
        self.assertEqual(raised.exception.audit["canonical_tree_sha256"],
                         raised.exception.audit["requirements_fingerprint"])

    def test_current_run_fingerprint_is_unverified_not_guessed(self):
        lite = tree("verified old Lite snapshot")
        old_lite_entry = self.add_suite("arc-bench-lite--bookstack", lite, "// lite",
                                        "official-snapshot:20260917-150121Z")
        old_lite_entry["requirements_fingerprint"] = (
            "4DC5389CD22A2340D32F771277C802267902721527BD811AE6B4A0D5CAC36F40")
        self.write_manifest([self.add_suite("arc-bench-web--bookstack", tree("web"), "// web"),
                             old_lite_entry])
        generic_tree = tree("platform runtime requirements")
        with patch("acceptance_identity.requirement_fingerprint",
                   return_value="5DD4F3C4226EE6E7426E9FF95526291F4663F2C1720BF411F33A0C8A54476F34"):
            with self.assertRaises(AcceptanceIdentityError) as raised:
                self.locate(generic_tree)
        audit = raised.exception.audit
        self.assertEqual(raised.exception.status, "identity_unverified")
        self.assertEqual([item["source"] for item in audit["task_key_observations"]],
                         ["requirements.task_key", "requirements.taskKey", "requirement_path_component"])
        self.assertTrue(all(not item["present"] for item in audit["task_key_observations"]))
        self.assertEqual(audit["matching_suites"], [])
        self.assertEqual(audit["requirements_fingerprint"],
                         "5DD4F3C4226EE6E7426E9FF95526291F4663F2C1720BF411F33A0C8A54476F34")
        lite_entry = next(item for item in audit["manifest_entries_considered"]
                          if item["task_key"] == "arc-bench-lite--bookstack")
        self.assertEqual(lite_entry["snapshot"], "official-snapshot:20260917-150121Z")
        self.assertEqual(lite_entry["requirements_fingerprint"],
                         "4DC5389CD22A2340D32F771277C802267902721527BD811AE6B4A0D5CAC36F40")
        self.assertIsNone(audit["selected_suite"])

    def test_explicit_wrong_family_key_and_fingerprint_mismatch_fails_closed(self):
        web, lite = tree("web"), tree("lite")
        self.write_manifest([self.add_suite("arc-bench-web--bookstack", web, "// web"),
                             self.add_suite("arc-bench-lite--bookstack", lite, "// lite")])
        wrong_family = dict(lite, task_key="arc-bench-web--bookstack")
        with self.assertRaises(AcceptanceIdentityError) as raised:
            self.locate(wrong_family)
        self.assertEqual(raised.exception.status, "identity_snapshot_mismatch")
        self.assertEqual(raised.exception.audit["task_key_source"], "requirements.task_key")
        self.assertEqual(raised.exception.audit["manifest_entry"]["task_key"], "arc-bench-web--bookstack")
        self.assertIsNone(raised.exception.audit["selected_suite"])

    def test_unknown_explicit_key_does_not_fall_back_to_matching_fingerprint(self):
        lite = tree("lite")
        self.write_manifest([self.add_suite("arc-bench-lite--bookstack", lite, "// lite")])
        unknown = dict(lite, task_key="arc-bench-unknown--bookstack")
        with self.assertRaises(AcceptanceIdentityError) as raised:
            self.locate(unknown)
        self.assertEqual(raised.exception.status, "identity_unverified")

    def test_exact_requirement_path_component_is_an_audited_key_source(self):
        lite = tree("lite")
        self.write_manifest([self.add_suite("arc-bench-lite--bookstack", lite, "// lite")])
        req = self.root / "arc-bench-lite--bookstack"
        req.mkdir()
        (req / "requirements.yaml").write_text(yaml.safe_dump(lite), encoding="utf-8")
        selected = locate_acceptance_suite(lite, req, self.bundle, [], self.logs.append)
        self.assertEqual(selected.audit["task_key_source"], "requirement_path_component")
        self.assertEqual(selected.audit["task_key_observations"][-1]["value"], "arc-bench-lite--bookstack")
        self.assertEqual(selected.audit["requirements_fingerprint"], requirement_fingerprint(lite))

    def test_conflicting_key_sources_fail_closed(self):
        lite = tree("lite", "atomic")
        lite["task_key"] = "arc-bench-lite--bookstack"
        self.write_manifest([self.add_suite("arc-bench-lite--bookstack", lite, "// lite"),
                             self.add_suite("arc-bench-web--bookstack", tree("web"), "// web")])
        req = self.root / "arc-bench-web--bookstack"
        req.mkdir()
        (req / "requirements.yaml").write_text(yaml.safe_dump(lite), encoding="utf-8")
        with self.assertRaises(AcceptanceIdentityError) as raised:
            locate_acceptance_suite(lite, req, self.bundle, [], self.logs.append)
        self.assertEqual(raised.exception.status, "identity_conflict")

    def test_explicit_task_key_must_match_current_registered_snapshot(self):
        older = tree("older snapshot")
        current = tree("current snapshot")
        self.write_manifest([self.add_suite("arc-bench-lite--bookstack", current, "// lite",
                                            "official-snapshot:20260918-000000Z")])
        older["task_key"] = "arc-bench-lite--bookstack"
        with self.assertRaises(AcceptanceIdentityError) as raised:
            self.locate(older)
        self.assertEqual(raised.exception.status, "identity_snapshot_mismatch")

    def test_fingerprint_matching_multiple_families_is_ambiguous(self):
        shared = tree("same tree")
        self.write_manifest([self.add_suite("arc-bench-web--bookstack", shared, "// web"),
                             self.add_suite("arc-bench-lite--bookstack", shared, "// lite")])
        with self.assertRaises(AcceptanceIdentityError) as raised:
            self.locate(shared)
        self.assertEqual(raised.exception.status, "identity_ambiguous")

    def test_matching_platform_suite_has_priority_and_empty_platform_falls_back(self):
        lite = tree("lite")
        entry = self.add_suite("arc-bench-lite--bookstack", lite, "// lite")
        self.write_manifest([entry])
        empty = self.root / "empty"
        empty.mkdir()
        fallback = self.locate(lite, [empty])
        self.assertEqual(fallback.audit["suite_source"], "bundled")
        platform = self.root / "platform"
        shutil.copytree(self.bundle / "public-tests" / entry["suite_path"], platform)
        selected = self.locate(lite, [platform])
        self.assertEqual(selected.audit["suite_source"], "platform")
        self.assertEqual(selected.path, platform.resolve())

    def test_nonempty_wrong_family_platform_suite_fails_closed(self):
        web, lite = tree("web"), tree("lite")
        web_entry = self.add_suite("arc-bench-web--bookstack", web, "// web")
        lite_entry = self.add_suite("arc-bench-lite--bookstack", lite, "// lite")
        self.write_manifest([web_entry, lite_entry])
        with self.assertRaises(AcceptanceIdentityError) as raised:
            self.locate(lite, [self.bundle / "public-tests" / web_entry["suite_path"]])
        self.assertEqual(raised.exception.status, "identity_suite_mismatch")

    def test_manifest_requires_snapshot_provenance_and_rejects_duplicate_task_versions(self):
        lite = tree("lite")
        entry = self.add_suite("arc-bench-lite--bookstack", lite, "// lite")
        for bad_snapshot in ("", "unknown:current"):
            with self.subTest(snapshot=bad_snapshot):
                self.write_manifest([dict(entry, snapshot=bad_snapshot)])
                with self.assertRaises(AcceptanceIdentityError) as invalid:
                    self.locate(lite)
                self.assertEqual(invalid.exception.status, "identity_manifest_invalid")
                self.assertIsNotNone(invalid.exception.audit["requirements_file_sha256"])
        self.write_manifest([entry, dict(entry, snapshot="official-snapshot:20260917-150120Z")])
        with self.assertRaises(AcceptanceIdentityError) as duplicate:
            self.locate(lite)
        self.assertEqual(duplicate.exception.status, "identity_manifest_ambiguous")

    def test_missing_requirements_file_is_unverified(self):
        lite = tree("lite")
        self.write_manifest([self.add_suite("arc-bench-lite--bookstack", lite, "// lite")])
        req = self.root / "tmp" / "arcbench" / "requirements-source"
        req.mkdir(parents=True)
        with self.assertRaises(AcceptanceIdentityError) as raised:
            locate_acceptance_suite(lite, req, self.bundle, [], self.logs.append)
        self.assertEqual(raised.exception.status, "identity_unverified")
        self.assertIsNone(raised.exception.audit["requirements_file_sha256"])

    def test_manifest_hashes_detect_spec_and_helper_tampering(self):
        lite = tree("lite")
        entry = self.add_suite("arc-bench-lite--bookstack", lite, "// lite")
        self.write_manifest([entry])
        suite = self.bundle / "public-tests" / entry["suite_path"]
        (suite / "helpers.ts").write_text("tampered", encoding="utf-8")
        with self.assertRaisesRegex(AcceptanceIdentityError, "identity_bundle_invalid"):
            self.locate(lite)
        (suite / "helpers.ts").write_text("// arc-bench-lite--bookstack", encoding="utf-8")
        (suite / "REQ-1.spec.ts").write_text("tampered", encoding="utf-8")
        with self.assertRaisesRegex(AcceptanceIdentityError, "identity_bundle_invalid"):
            self.locate(lite)


if __name__ == "__main__":
    unittest.main()
