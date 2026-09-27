import queue
import unittest
from pathlib import Path
from unittest import mock

import octos_stdio as os_mod


class FakePipe:
    """Minimal stdout/stderr stand-in: iterable and closeable so the reader
    threads exit immediately instead of blocking on a real subprocess."""

    def __iter__(self):
        return iter(())

    def close(self):
        pass


class FakeProc:
    def __init__(self, *a, **kw):
        self.stdin = FakePipe()
        self.stdout = FakePipe()
        self.stderr = FakePipe()

    def poll(self):
        return None


class PopenEncodingTests(unittest.TestCase):
    def test_should_decode_octos_output_as_utf8_not_platform_codepage(self):
        # Regression: octos emits UTF-8. With text=True but no explicit encoding,
        # Windows decodes with gbk and the reader thread dies on the first
        # non-ASCII byte (cloud/keep run: UnicodeDecodeError 0xa6). Pin utf-8.
        captured = {}

        def fake_popen(cmd, **kw):
            captured.update(kw)
            return FakeProc()

        with mock.patch.object(os_mod.subprocess, "Popen", side_effect=fake_popen):
            os_mod.OctosStdioSession("octos", Path("."), {}, Path("."))

        self.assertEqual(captured.get("encoding"), "utf-8")
        self.assertTrue(captured.get("text"))
        self.assertEqual(captured.get("errors"), "replace")


if __name__ == "__main__":
    unittest.main()
