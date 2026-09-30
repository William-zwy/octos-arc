import json
import tempfile
import unittest
from pathlib import Path

from run_controls import CheckpointStore


class CheckpointStoreTests(unittest.TestCase):
    def test_write_uses_numbered_snapshot_and_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = CheckpointStore(Path(tmp))
            path = store.write({"reason": "node_start", "node_id": "synthetic"})
            self.assertTrue(path.is_file())
            manifest = json.loads((Path(tmp) / ".arc/checkpoints/manifest.json").read_text())
            self.assertEqual(manifest["latest"], "cp-000001")
            record = json.loads(path.read_text())
            self.assertEqual(record["schema_version"], 1)
            self.assertEqual(record["node_id"], "synthetic")

    def test_each_write_preserves_previous_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = CheckpointStore(Path(tmp))
            first = store.write({"phase": "first"})
            second = store.write({"phase": "second"})
            self.assertNotEqual(first, second)
            self.assertEqual(json.loads(first.read_text())["phase"], "first")
            self.assertEqual(json.loads(second.read_text())["phase"], "second")


if __name__ == "__main__":
    unittest.main()
