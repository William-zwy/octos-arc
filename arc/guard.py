"""Guard rules (A7): watch one turn's tool events and the final message and
produce short corrective sentences for the next prompt.

Detects: completion claims with no verification command; the same tool error
three times in a row; writes into protected paths (specs, requirements, .arc).
"""

from __future__ import annotations

import re

_VERIFY = re.compile(r"\b(npm run build|npm start|npm run start|node \S+\.js|curl\b|playwright|wget\b|node --check)", re.I)
_CLAIM = re.compile(r"\b(implemented|complete[d]?|done|verified|passes|passing|finished|working)\b|✅", re.I)
_WRITE_TOOLS = {"write_file", "edit_file", "apply_patch", "create_file", "append_file"}
_SHELL_TOOLS = {"bash", "shell", "exec", "run_command"}
_REDIRECT = re.compile(r"(?<!\d)>>?\s*(?!/dev/null\b)(\S+)")
_TEE_WRITE = re.compile(r"\btee\s+(?:-a\s+)?(?!/dev/null\b)(\S+)", re.I)
_VERIFY_KIND = (
    ("build", re.compile(r"\bnpm\s+(?:run\s+)?build\b|\bnode\s+--check\b", re.I)),
    ("start", re.compile(r"\bnpm\s+(?:run\s+)?start\b|\bnode\s+\S+\.js\b", re.I)),
    ("request", re.compile(r"\bcurl\b|\bwget\b|\bplaywright\b", re.I)),
)


class TurnMonitor:
    def __init__(self, protected_prefixes: list[str], repeat_threshold: int = 3,
                 expect_verification: bool = True, allowed_prefixes: list[str] | None = None) -> None:
        self.protected = [p for p in protected_prefixes if p]
        self.allowed = [p for p in (allowed_prefixes or []) if p]
        self.repeat_threshold = repeat_threshold
        self.expect_verification = expect_verification
        self.wrote_files = False
        self.verified = False
        self.tool_calls = 0
        self.errors_in_a_row = 0
        self._last_error = None
        self._max_repeat = 0
        self._repeated_error = ""
        self.protected_writes: list[str] = []
        self.written_paths: list[str] = []
        self._pending: dict[str, tuple[str, dict]] = {}
        # A tool being started is not proof that it wrote a file or that a
        # verification command passed.  Keep those claims pending until the
        # matching completion event reports success.
        self._pending_writes: set[str] = set()
        self._pending_verifications: set[str] = set()
        self._final_text = ""
        self._event_seq = 0
        self._last_write_seq = 0
        self._last_verification_seq = 0
        self.verification_kinds: set[str] = set()
        self._verification_seq_by_kind: dict[str, int] = {}

    # -- events -----------------------------------------------------------
    def observe(self, method: str, params: dict) -> None:
        self._event_seq += 1
        if method == "tool/started":
            self.tool_calls += 1
            name = str(params.get("tool_name") or "")
            args = params.get("arguments") or {}
            self._pending[str(params.get("tool_call_id"))] = (name, args)
            if name in _WRITE_TOOLS:
                self._pending_writes.add(str(params.get("tool_call_id")))
                self._note_path(str(args.get("path") or args.get("file_path") or ""))
            elif name in _SHELL_TOOLS:
                cmd = str(args.get("cmd") or args.get("command") or "")
                if _VERIFY.search(cmd):
                    self._pending_verifications.add(str(params.get("tool_call_id")))
                has_redirect_write = bool(_REDIRECT.search(cmd) or _TEE_WRITE.search(cmd))
                has_copy_write = bool(re.search(r"\b(cp|mv)\s+\S+\s+\S+", cmd))
                has_edit_write = bool(re.search(r"\bsed\s+-i(?:\S*)?\s", cmd))
                if has_redirect_write or has_copy_write or has_edit_write:
                    self._pending_writes.add(str(params.get("tool_call_id")))
                    for m in list(_REDIRECT.finditer(cmd)) + list(_TEE_WRITE.finditer(cmd)):
                        self._note_path(m.group(1).strip("'\""))
        elif method == "tool/completed":
            call_id = str(params.get("tool_call_id"))
            ok = bool(params.get("success", True))
            if ok and call_id in self._pending_writes:
                self.wrote_files = True
                self._last_write_seq = self._event_seq
            if ok and call_id in self._pending_verifications:
                self._last_verification_seq = self._event_seq
                for kind, pattern in _VERIFY_KIND:
                    if pattern.search(str(self._pending.get(call_id, ("", {}))[1].get("cmd") or "")):
                        self.verification_kinds.add(kind)
                        self._verification_seq_by_kind[kind] = self._event_seq
                self.verified = self._last_verification_seq > self._last_write_seq
            self._pending_writes.discard(call_id)
            self._pending_verifications.discard(call_id)
            preview = str(params.get("output_preview") or "")[:300]
            if not ok:
                key = re.sub(r"\d+", "#", preview)
                if key == self._last_error:
                    self.errors_in_a_row += 1
                else:
                    self._last_error, self.errors_in_a_row = key, 1
                if self.errors_in_a_row > self._max_repeat:
                    self._max_repeat, self._repeated_error = self.errors_in_a_row, preview
            else:
                self._last_error, self.errors_in_a_row = None, 0

    def _note_path(self, path: str) -> None:
        if not path:
            return
        self.written_paths.append(path)
        if any(path.startswith(a) or f"/{a}" in path for a in self.allowed):
            return
        for prefix in self.protected:
            if path.startswith(prefix) or f"/{prefix}" in path:
                self.protected_writes.append(path)
                break

    def finish(self, final_text: str) -> None:
        self._final_text = final_text or ""

    @property
    def verification_complete(self) -> bool:
        required = {"build", "start", "request"}
        return (self.verified and required.issubset(self.verification_kinds)
                and all(self._verification_seq_by_kind.get(kind, 0) > self._last_write_seq for kind in required))

    # -- verdicts ---------------------------------------------------------
    def corrections(self) -> list[str]:
        out: list[str] = []
        if self.expect_verification and (self.wrote_files or self.written_paths) \
                and not self.verification_complete and _CLAIM.search(self._final_text):
            out.append("Your previous turn claimed completion without running any build, start or "
                       "request command after the last write. Never declare a step done before executing "
                       "`npm run build`, starting the backend on the smoke port and exercising the endpoint "
                       "with curl or Playwright.")
        if self._max_repeat >= self.repeat_threshold:
            out.append(f"You hit the same error {self._max_repeat} times in a row "
                       f"({self._repeated_error[:160]!r}). Stop repeating the command; diagnose the "
                       "root cause (read the file / port / path involved) and change approach.")
        if self.protected_writes:
            out.append("You modified protected files that must never change: "
                       + ", ".join(sorted(set(self.protected_writes))[:5])
                       + ". Revert nothing yourself; only touch frontend/ and backend/ from now on.")
        return out
