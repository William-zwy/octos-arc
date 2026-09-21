import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from build_identity import (BuildIdentityError, embed_identity, file_sha256,
                            make_identity, payload_tree_identity, read_archive_identity,
                            verify_archive_identity, write_release_provenance)
from package_shape import (AGENT_REQUIRED_DIRS, AGENT_REQUIRED_FILES, inventory,
                           write_report)


COMMIT = "1" * 40


def write_payload(archive: Path, marker: str = "one") -> None:
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as handle:
        handle.writestr("main.py", marker)
        handle.writestr("runtime/helper.py", "helper")


def write_agent_payload(archive: Path) -> None:
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as handle:
        for name in AGENT_REQUIRED_FILES:
            if name != "agent-build.json":
                handle.writestr(name, f"payload:{name}")
        for name in AGENT_REQUIRED_DIRS:
            handle.writestr(f"{name}/fixture.txt", "fixture")


class BuildIdentityTests(unittest.TestCase):
    def test_identity_is_stable_and_payload_sensitive(self):
        with tempfile.TemporaryDirectory() as tmp:
            first = Path(tmp) / "first.zip"
            same = Path(tmp) / "same.zip"
            changed = Path(tmp) / "changed.zip"
            write_payload(first)
            write_payload(same)
            write_payload(changed, "two")

            first_hash, first_count = payload_tree_identity(first)
            same_hash, same_count = payload_tree_identity(same)
            changed_hash, changed_count = payload_tree_identity(changed)
            first_identity = make_identity(COMMIT, first_hash, first_count)
            same_identity = make_identity(COMMIT, same_hash, same_count)
            changed_identity = make_identity(COMMIT, changed_hash, changed_count)

            self.assertEqual(first_identity, same_identity)
            self.assertNotEqual(first_identity["payload_tree_sha256"], changed_identity["payload_tree_sha256"])
            self.assertNotEqual(first_identity["build_id"], changed_identity["build_id"])

    def test_embedded_identity_detects_post_embed_payload_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "agent.zip"
            write_payload(archive)
            identity = embed_identity(archive, COMMIT)

            self.assertEqual(read_archive_identity(archive), identity)
            self.assertEqual(verify_archive_identity(archive), identity)
            with zipfile.ZipFile(archive, "a") as handle:
                handle.writestr("later.txt", "changed")
            with self.assertRaisesRegex(BuildIdentityError, "payload tree SHA-256"):
                verify_archive_identity(archive)

    def test_release_sidecars_bind_identity_shape_and_full_zip_sha(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = root / "octos-arc-agent.zip"
            shape_path = root / "octos-arc-agent.shape.json"
            release_path = root / "octos-arc-agent.release.json"
            checksum_path = root / "octos-arc-agent.zip.sha256"
            write_agent_payload(archive)
            identity = embed_identity(archive, COMMIT)
            shape = {
                "schema_version": 1,
                "contract": "arc_agent_bundle_v1",
                "first_missing_stage": None,
                "ok": True,
                "stages": [inventory(archive, "agent_zip", "agent")],
                "agent_build": identity,
            }
            write_report(shape, shape_path)

            release = write_release_provenance(
                archive, shape_path, release_path, checksum_path,
            )

            self.assertEqual(release["build_identity"], identity)
            self.assertEqual(release["artifact"]["sha256"], file_sha256(archive))
            self.assertEqual(release["shape_manifest"]["sha256"], file_sha256(shape_path))
            self.assertEqual(json.loads(release_path.read_text()), release)
            self.assertEqual(
                checksum_path.read_text(),
                f"{file_sha256(archive)}  {archive.name}\n",
            )


if __name__ == "__main__":
    unittest.main()
