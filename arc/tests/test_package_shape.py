import shutil
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

import main as agent_main
from package_shape import (AGENT_REQUIRED_DIRS, AGENT_REQUIRED_FILES, PackageShapeError,
                           inspect_pipeline, inventory, require_report)


FIXTURES = Path(__file__).parent / "fixtures" / "package-shape"


def zip_tree(source: Path, destination: Path, prefix: str = "") -> None:
    with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(source.rglob("*")):
            if path.is_file():
                archive.write(path, prefix + path.relative_to(source).as_posix())


class AppPipelineShapeTests(unittest.TestCase):
    def test_known_good_workspace_staging_and_archive_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            workspace = root / "workspace"
            staging = root / "staging"
            archive = root / "template.zip"
            shutil.copytree(FIXTURES / "known-good", workspace)
            shutil.copytree(workspace, staging)
            zip_tree(staging, archive)

            report = inspect_pipeline(workspace, staging, archive)

            self.assertTrue(report["ok"])
            self.assertIsNone(report["first_missing_stage"])
            self.assertEqual([stage["entry_count"] for stage in report["stages"]], [4, 4, 2])
            require_report(report)

    def test_missing_backend_fixture_names_first_broken_stage(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            workspace = root / "workspace"
            staging = root / "staging"
            archive = root / "template.zip"
            shutil.copytree(FIXTURES / "known-good", workspace)
            shutil.copytree(FIXTURES / "missing-backend", staging)
            zip_tree(staging, archive)

            report = inspect_pipeline(workspace, staging, archive)

            self.assertFalse(report["ok"])
            self.assertEqual(report["first_missing_stage"], "staging")
            self.assertEqual(report["stages"][1]["missing"], ["backend/"])
            with self.assertRaisesRegex(PackageShapeError, "staging.*backend/"):
                require_report(report)

    def test_nested_app_directories_do_not_satisfy_root_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = root / "nested.zip"
            zip_tree(FIXTURES / "known-good", archive, "nested/")

            result = inventory(archive, "final_zip")

            self.assertFalse(result["ok"])
            self.assertEqual(result["missing"], ["frontend/", "backend/"])

    def test_unsafe_archive_entry_fails_even_when_root_shape_is_present(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive_path = Path(tmp) / "unsafe.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("frontend/package.json", "{}")
                archive.writestr("backend/package.json", "{}")
                archive.writestr("../escape.txt", "no")

            result = inventory(archive_path, "final_zip")

            self.assertFalse(result["ok"])
            self.assertEqual(result["missing"], [])
            self.assertEqual(result["unsafe_entries"], ["../escape.txt"])


class AgentBundleShapeTests(unittest.TestCase):
    def test_agent_archive_requires_runtime_files_at_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive_path = Path(tmp) / "agent.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                for name in AGENT_REQUIRED_FILES:
                    archive.writestr(name, "fixture")
                for name in AGENT_REQUIRED_DIRS:
                    archive.writestr(f"{name}/fixture.txt", "fixture")

            result = inventory(archive_path, "agent_zip", "agent")

            self.assertTrue(result["ok"])
            self.assertEqual(result["missing"], [])

    def test_agent_archive_rejects_main_under_wrapper_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive_path = Path(tmp) / "wrapped-agent.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("bundle/main.py", "fixture")

            result = inventory(archive_path, "agent_zip", "agent")

            self.assertFalse(result["ok"])
            self.assertIn("main.py", result["missing"])


class PostflightShapeTests(unittest.TestCase):
    def test_postflight_freezes_workspace_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "workspace"
            shutil.copytree(FIXTURES / "known-good", workspace)

            with patch.object(agent_main, "log"):
                agent_main._postflight_structure_check(workspace, strict=True)

            self.assertTrue((workspace / ".arc" / "package-shape" / "pipeline.json").is_file())

    def test_strict_postflight_rejects_missing_backend(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "workspace"
            shutil.copytree(FIXTURES / "missing-backend", workspace)

            with patch.object(agent_main, "log"), self.assertRaisesRegex(RuntimeError, "backend/"):
                agent_main._postflight_structure_check(workspace, strict=True)


if __name__ == "__main__":
    unittest.main()
