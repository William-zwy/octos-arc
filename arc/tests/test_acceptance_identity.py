from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

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

    def add_suite(self, task_key: str, requirement_tree: dict, spec_text: str) -> dict:
        suite = self.bundle / "public-tests" / task_key
        suite.mkdir()
        (suite / "REQ-1.spec.ts").write_text(spec_text, encoding="utf-8")
        (suite / "helpers.ts").write_text(f"// {task_key}", encoding="utf-8")
        observed = inspect_suite(suite)
        return {
            "suite_path": task_key, "task_key": task_key,
            "competition": task_key.split("--", 1)[0], "snapshot": "test-fixture",
            "requirements_fingerprint": requirement_fingerprint(requirement_tree),
            "spec_count": observed["spec_count"], "specs_sha256": observed["specs_sha256"],
            "helper_sha256": observed["helper_sha256"],
        }

    def write_manifest(self, entries: list[dict]) -> None:
        (self.bundle / "public-tests" / "manifest.json").write_text(
            json.dumps({"schema_version": 2, "suites": entries}), encoding="utf-8")

    def locate(self, requirement_tree: dict, candidates: list[Path] | None = None):
        req = self.root / "generic-requirements-source"
        req.mkdir(exist_ok=True)
        return locate_acceptance_suite(requirement_tree, req, self.bundle, candidates or [], self.logs.append)

    def test_same_root_title_routes_web_and_lite_to_their_exact_suites(self):
        web, lite = tree("web description"), tree("lite description")
        entries = [self.add_suite("arc-bench-web--bookstack", web, "// web"),
                   self.add_suite("arc-bench-lite--bookstack", lite, "// lite")]
        self.write_manifest(entries)
        self.assertEqual(self.locate(web).audit["task_key"], "arc-bench-web--bookstack")
        lite_selection = self.locate(lite)
        self.assertEqual(lite_selection.audit["task_key"], "arc-bench-lite--bookstack")
        self.assertNotIn("arc-bench-web--bookstack", str(lite_selection.path))

    def test_title_only_identity_fails_closed(self):
        web, lite = tree("web description"), tree("lite description")
        self.write_manifest([self.add_suite("arc-bench-web--bookstack", web, "// web"),
                             self.add_suite("arc-bench-lite--bookstack", lite, "// lite")])
        with self.assertRaisesRegex(AcceptanceIdentityError, "acceptance_identity_ambiguous"):
            self.locate({"id": "ROOT", "name": web["name"], "type": "FOLDER"})

    def test_fingerprint_is_yaml_representation_stable_and_semantic_sensitive(self):
        unix = "id: ROOT\nname: Demo\ntype: FOLDER\ndescription: same\ndependencies: []\nchildren: []\n"
        windows = unix.replace("\n", "\r\n")
        quoted = "name: 'Demo'\r\ntype: FOLDER\r\nid: ROOT\r\nchildren: []\r\ndependencies: []\r\ndescription: same\r\n"
        self.assertEqual(requirement_fingerprint(yaml.safe_load(unix)),
                         requirement_fingerprint(yaml.safe_load(windows)))
        self.assertEqual(requirement_fingerprint(yaml.safe_load(unix)),
                         requirement_fingerprint(yaml.safe_load(quoted)))
        changed = yaml.safe_load(unix); changed["description"] = "different"
        self.assertNotEqual(requirement_fingerprint(yaml.safe_load(unix)),
                            requirement_fingerprint(changed))

    def test_matching_platform_suite_has_priority_and_empty_platform_falls_back(self):
        lite = tree("lite")
        entry = self.add_suite("arc-bench-lite--bookstack", lite, "// lite")
        self.write_manifest([entry])
        empty = self.root / "empty"; empty.mkdir()
        fallback = self.locate(lite, [empty])
        self.assertEqual(fallback.audit["source"], "bundled")
        platform = self.root / "platform"
        shutil.copytree(self.bundle / "public-tests" / entry["suite_path"], platform)
        selected = self.locate(lite, [platform])
        self.assertEqual(selected.audit["source"], "platform")
        self.assertEqual(selected.path, platform.resolve())

    def test_nonempty_wrong_family_platform_suite_fails_closed(self):
        web, lite = tree("web"), tree("lite")
        web_entry = self.add_suite("arc-bench-web--bookstack", web, "// web")
        lite_entry = self.add_suite("arc-bench-lite--bookstack", lite, "// lite")
        self.write_manifest([web_entry, lite_entry])
        with self.assertRaisesRegex(AcceptanceIdentityError, "acceptance_identity_mismatch"):
            self.locate(lite, [self.bundle / "public-tests" / web_entry["suite_path"]])

    def test_explicit_task_key_must_agree_with_fingerprint(self):
        web, lite = tree("web"), tree("lite")
        entries = [self.add_suite("arc-bench-web--bookstack", web, "// web"),
                   self.add_suite("arc-bench-lite--bookstack", lite, "// lite")]
        self.write_manifest(entries)
        req = self.root / "arc-bench-lite--bookstack"; req.mkdir()
        with self.assertRaisesRegex(AcceptanceIdentityError, "acceptance_identity_mismatch"):
            locate_acceptance_suite(web, req, self.bundle, [], self.logs.append)

    def test_manifest_hashes_detect_spec_and_helper_tampering(self):
        lite = tree("lite")
        entry = self.add_suite("arc-bench-lite--bookstack", lite, "// lite")
        self.write_manifest([entry])
        suite = self.bundle / "public-tests" / entry["suite_path"]
        (suite / "helpers.ts").write_text("tampered", encoding="utf-8")
        with self.assertRaisesRegex(AcceptanceIdentityError, "acceptance_identity_invalid"):
            self.locate(lite)
        (suite / "helpers.ts").write_text("// arc-bench-lite--bookstack", encoding="utf-8")
        (suite / "REQ-1.spec.ts").write_text("tampered", encoding="utf-8")
        with self.assertRaisesRegex(AcceptanceIdentityError, "acceptance_identity_invalid"):
            self.locate(lite)

    def test_duplicate_task_keys_make_manifest_ambiguous(self):
        lite = tree("lite")
        entry = self.add_suite("arc-bench-lite--bookstack", lite, "// lite")
        self.write_manifest([entry, dict(entry)])
        with self.assertRaisesRegex(AcceptanceIdentityError, "acceptance_identity_ambiguous"):
            self.locate(lite)


if __name__ == "__main__":
    unittest.main()
