"""Small, task-agnostic run controls used by the ARC harness.

The controls deliberately live outside prompt text: quota gates and checkpoints
must still work when the model ignores a Skill or a turn is interrupted.
"""

from __future__ import annotations

import json
import os
import tempfile
import time
from pathlib import Path
from typing import Any


def atomic_json_write(path: Path, payload: dict[str, Any]) -> None:
    """Write a complete JSON file before replacing the previous snapshot."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=2, sort_keys=True)
            fh.write("\n")
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp_name, path)
    finally:
        try:
            tmp_path = Path(tmp_name)
            if tmp_path.exists():
                tmp_path.unlink()
        except OSError:
            pass


class CheckpointStore:
    """Append numbered snapshots and point a manifest at the latest valid one."""

    def __init__(self, output_dir: Path) -> None:
        self.root = output_dir / ".arc" / "checkpoints"
        self.manifest = self.root / "manifest.json"
        self.sequence = 0

    def write(self, payload: dict[str, Any]) -> Path:
        self.sequence += 1
        checkpoint_id = f"cp-{self.sequence:06d}"
        record = dict(payload)
        record.update({"schema_version": 1, "checkpoint_id": checkpoint_id,
                       "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())})
        path = self.root / f"{checkpoint_id}.json"
        atomic_json_write(path, record)
        atomic_json_write(self.manifest, {"schema_version": 1, "latest": checkpoint_id,
                                          "path": str(path.relative_to(self.root.parent.parent))})
        return path
