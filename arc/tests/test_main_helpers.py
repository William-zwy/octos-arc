import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from main import (OctosDriver, PermanentAuthenticationError, describe_node, folder_descendants,
                  inline_sources, inline_spec_text, unchanged_node_ids)
import main as m


def node(node_id, description, deps=()):
    return {"id": node_id, "type": "ATOMIC", "name": node_id, "description": description,
            "dependencies": list(deps), "scenarios": [{"name": "s", "steps": [{"keyword": "GIVEN", "content": "x"}]}]}


class EvolutionDiffTests(unittest.TestCase):
    def test_should_keep_nodes_whose_content_matches_previous_requirement_table(self):
        current = [node("REQ-1", "same"), node("REQ-2", "changed"), node("REQ-3", "new", ["REQ-1"])]
        previous = {
            "REQ-1": {"req_id": "REQ-1", "id": "REQ-1", "name": "REQ-1", "description": "same", "dependencies": [],
                      "scenarios": [{"name": "s", "steps": [{"keyword": "GIVEN", "content": "x"}]}]},
            "REQ-2": {"req_id": "REQ-2", "id": "REQ-2", "name": "REQ-2", "description": "old", "dependencies": [],
                      "scenarios": [{"name": "s", "steps": [{"keyword": "GIVEN", "content": "x"}]}]},
        }
        self.assertEqual(unchanged_node_ids(current, previous), {"REQ-1"})

    def test_should_treat_everything_as_changed_without_previous_table(self):
        self.assertEqual(unchanged_node_ids([node("REQ-1", "a")], {}), set())


class DescribeNodeTests(unittest.TestCase):
    def test_should_render_scenarios_and_dependencies(self):
        text = describe_node(node("REQ-2", "desc", ["REQ-1"]))
        self.assertIn("ID: REQ-2", text)
        self.assertIn("GIVEN x", text)
        self.assertIn("Depends on: REQ-1", text)


if __name__ == "__main__":
    unittest.main()


class TransientTests(unittest.TestCase):
    def test_should_not_retry_own_turn_timeouts(self):
        self.assertFalse(OctosDriver._transient("octos turn timed out"))
        self.assertFalse(OctosDriver._transient("octos timed out after 900s"))

    def test_should_retry_provider_errors(self):
        self.assertTrue(OctosDriver._transient("HTTP 503 Service Temporarily Unavailable"))
        self.assertTrue(OctosDriver._transient("HTTP 429 rate limit"))
        self.assertTrue(OctosDriver._transient("failed to send streaming request"))

    def test_should_not_retry_permanent_authentication_errors(self):
        for message in ("HTTP 401 invalid_api_key", "HTTP 403 Forbidden",
                        "authentication failed", "Unauthorized"):
            with self.subTest(message=message):
                self.assertFalse(OctosDriver._transient(message))


class EndpointProbeTests(unittest.TestCase):
    class EndpointError(Exception):
        def __init__(self, code, message):
            super().__init__(message)
            self.code = code

    class Response:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        @staticmethod
        def read():
            return b"OK"

    def run_probe(self, outcomes, attempts=3):
        calls = []
        sleeps = []

        def urlopen(_request, timeout):
            calls.append(timeout)
            outcome = outcomes.pop(0)
            if isinstance(outcome, Exception):
                raise outcome
            return outcome

        with patch.dict(os.environ, {"OPENAI_API_KEY": "secret", "OPENAI_BASE_URL": "https://provider.invalid"}):
            m.probe_endpoint(urlopen=urlopen, sleep_fn=sleeps.append, attempts=attempts, retry_seconds=0)
        return calls, sleeps

    def test_should_fail_fast_for_401_and_403(self):
        for status in (401, 403):
            with self.subTest(status=status):
                outcomes = [self.EndpointError(status, "invalid_api_key")]
                with self.assertRaises(PermanentAuthenticationError):
                    self.run_probe(outcomes)
                self.assertEqual(outcomes, [])

    def test_should_retry_429_then_succeed(self):
        calls, sleeps = self.run_probe([self.EndpointError(429, "rate limit"), self.Response()])
        self.assertEqual((len(calls), sleeps), (2, [0]))

    def test_should_stop_after_bounded_503_retries(self):
        outcomes = [self.EndpointError(503, "unavailable") for _ in range(3)]
        with self.assertRaisesRegex(RuntimeError, "after 3 transient attempt"):
            self.run_probe(outcomes)
        self.assertEqual(outcomes, [])

    def test_should_retry_network_timeout_then_succeed(self):
        calls, sleeps = self.run_probe([TimeoutError("connection timed out"), self.Response()])
        self.assertEqual((len(calls), sleeps), (2, [0]))


class SkeletonAuthenticationTests(unittest.TestCase):
    def test_should_stop_after_first_permanent_authentication_failure(self):
        import argparse
        from pathlib import Path
        with tempfile.TemporaryDirectory() as tmp:
            flow = m.Flow(argparse.Namespace(web_port=3000), Path(tmp), Path(tmp))
            calls = []

            def fail_auth(*_args, **_kwargs):
                calls.append(True)
                return False, "HTTP 401 invalid_api_key"

            flow.turn = fail_auth
            with self.assertRaises(PermanentAuthenticationError):
                flow.skeleton({})
            self.assertEqual(len(calls), 1)


class EntrypointAuthenticationTests(unittest.TestCase):
    def test_should_persist_identity_and_return_two_before_generation_for_401_and_403(self):
        identity = m.make_identity("1" * 40, "2" * 64, 7)
        for status in (401, 403):
            with self.subTest(status=status), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                requirements = root / "requirements"
                requirements.mkdir()
                output = root / "output"
                stdout = io.StringIO()
                with patch.object(m, "_bundle_build_identity", return_value=identity), \
                        patch.object(m, "probe_endpoint",
                                     side_effect=PermanentAuthenticationError(f"HTTP {status}")) as probe, \
                        patch.object(m, "Flow") as flow, \
                        patch.object(sys, "argv", ["main.py", str(requirements),
                                                   "--output-dir", str(output)]), \
                        patch.dict(os.environ, {
                            "OPENAI_API_KEY": "top-secret-value",
                            "OPENAI_BASE_URL": "https://provider.invalid/v1",
                        }, clear=True), redirect_stdout(stdout):
                    self.assertEqual(m.main(), 2)

                probe.assert_called_once_with()
                flow.assert_not_called()
                text = stdout.getvalue()
                self.assertLess(text.index("ARC_AGENT_IDENTITY "), text.index("[probe]"))
                self.assertNotIn("top-secret-value", text)
                self.assertNotIn("len=", text)
                self.assertEqual(
                    json.loads((output / ".arc" / "agent-build.json").read_text()), identity,
                )
                pipeline = json.loads(
                    (output / ".arc" / "package-shape" / "pipeline.json").read_text()
                )
                self.assertEqual(pipeline["agent_build"], identity)
                self.assertEqual(pipeline["status"], "initialized_before_provider_probe")

    def test_known_good_mock_path_preserves_identity_through_shape_gate(self):
        identity = m.make_identity("3" * 40, "4" * 64, 9)

        class KnownGoodFlow:
            def __init__(self, _args, output_dir, _requirements):
                self.output_dir = output_dir

            def run(self):
                (self.output_dir / "frontend").mkdir()
                (self.output_dir / "backend").mkdir()
                (self.output_dir / "frontend" / "package.json").write_text("{}")
                (self.output_dir / "backend" / "package.json").write_text("{}")
                m._postflight_structure_check(self.output_dir, strict=True)
                return 0

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            requirements = root / "requirements"
            requirements.mkdir()
            output = root / "output"
            with patch.object(m, "_bundle_build_identity", return_value=identity), \
                    patch.object(m, "probe_endpoint") as probe, \
                    patch.object(m, "Flow", KnownGoodFlow), \
                    patch.object(sys, "argv", ["main.py", str(requirements),
                                               "--output-dir", str(output)]), \
                    patch.dict(os.environ, {}, clear=True), \
                    patch.object(m, "log"):
                self.assertEqual(m.main(), 0)

            probe.assert_called_once_with()
            self.assertTrue((output / "frontend").is_dir())
            self.assertTrue((output / "backend").is_dir())
            pipeline = json.loads(
                (output / ".arc" / "package-shape" / "pipeline.json").read_text()
            )
            self.assertTrue(pipeline["ok"])
            self.assertEqual(pipeline["agent_build"], identity)


class FolderDescendantTests(unittest.TestCase):
    def test_should_map_every_folder_to_its_atomic_leaves(self):
        tree = {"id": "ROOT", "type": "FOLDER", "children": [
            {"id": "F-1", "type": "FOLDER", "children": [node("REQ-1", "a"), node("REQ-2", "b")]},
            node("REQ-3", "c")]}
        self.assertEqual(folder_descendants(tree), {"F-1": ["REQ-1", "REQ-2"], "ROOT": ["REQ-1", "REQ-2", "REQ-3"]})


class SetupPlaywrightTests(unittest.TestCase):
    """Regression for cloud run d116ad5e3aa0: the private-install branch of
    setup_playwright must unpack (root, env_extra) and expose cleanup."""

    def test_should_use_private_install_tuple_and_clean_it_up(self):
        import argparse, tempfile
        from pathlib import Path
        import main as m
        with tempfile.TemporaryDirectory() as tmp:
            tests = Path(tmp) / "tests"; tests.mkdir(); (tests / "REQ-1.spec.ts").write_text("x")
            fake_root = Path(tmp) / "pw"; (fake_root / "node_modules" / "@playwright" / "test").mkdir(parents=True)
            flow = m.Flow(argparse.Namespace(web_port=3000), Path(tmp) / "out", Path(tmp) / "req")
            flow.tests_dir = tests
            calls = {}
            def fake_ensure(install_root, log, timeout=540, version="1.63.0"):
                calls["version"] = version
                return fake_root, {"PLAYWRIGHT_BROWSERS_PATH": str(install_root / "browsers")}
            saved = (m.find_playwright_root, m.find_playwright_by_search, m.ensure_playwright)
            m.find_playwright_root = lambda cands: fake_root if cands == [fake_root] else None
            m.find_playwright_by_search = lambda log: None
            m.ensure_playwright = fake_ensure
            try:
                flow.setup_playwright()
            finally:
                m.find_playwright_root, m.find_playwright_by_search, m.ensure_playwright = saved
            self.assertEqual(calls["version"], "1.63.0")
            self.assertIsNotNone(flow.runner)
            self.assertEqual(flow.runner.root, fake_root)
            self.assertIn("PLAYWRIGHT_BROWSERS_PATH", flow.runner.env_extra)
            private = flow.private_playwright
            self.assertTrue(private.exists())
            flow.cleanup_playwright()
            self.assertFalse(private.exists())


class InlineSpecTests(unittest.TestCase):
    def test_should_quote_files_within_budget_and_bail_when_too_big(self):
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as tmp:
            tests = Path(tmp); (tests / "support").mkdir()
            (tests / "REQ-1.spec.ts").write_text("spec body"); (tests / "support" / "e2e.ts").write_text("helper")
            text = inline_spec_text(tests, ["REQ-1.spec.ts", "support/e2e.ts"], 1000)
            self.assertIn("--- REQ-1.spec.ts ---\nspec body", text)
            self.assertIn("--- support/e2e.ts ---\nhelper", text)
            self.assertEqual(inline_spec_text(tests, ["REQ-1.spec.ts", "support/e2e.ts"], 10), "")


class InlineSourcesTests(unittest.TestCase):
    def test_should_quote_small_files_and_omit_those_over_budget(self):
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); (root / "backend").mkdir(); (root / "frontend" / "src").mkdir(parents=True)
            (root / "backend" / "server.js").write_text("x" * 100); (root / "frontend" / "src" / "index.html").write_text("<p>hi</p>")
            (root / "frontend" / "node_modules").mkdir(); (root / "frontend" / "node_modules" / "a.js").write_text("no")
            text = inline_sources(root, max_chars=50)
            self.assertIn("--- frontend/src/index.html ---\n<p>hi</p>", text)
            self.assertIn("backend/server.js --- (omitted, 100 chars", text)
            self.assertNotIn("node_modules", text)


class FailureNormalizationTests(unittest.TestCase):
    def test_should_treat_digests_differing_only_in_numbers_as_identical(self):
        import re
        a = "Observation: TIMED OUT after 4136 ms ... Expected: \"2\" Received: \"\""
        b = "Observation: TIMED OUT after 4144 ms ... Expected: \"2\" Received: \"\""
        self.assertEqual(re.sub(r"\d+", "#", a), re.sub(r"\d+", "#", b))


class RouteDiagnosticsTests(unittest.TestCase):
    def test_should_pass_bounded_route_hint_to_existing_repair_digest(self):
        import argparse, tempfile
        from pathlib import Path
        from acceptance import RunSummary, TestOutcome
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "backend").mkdir()
            (root / "backend/server.js").write_text(
                "if (pathname === '/shelf/edit' && req.method === 'GET') {}", encoding="utf-8")
            flow = m.Flow(argparse.Namespace(web_port=3000), root, root)
            flow.designs["REQ-1"] = {"routes": [
                {"method": "GET", "path": "/shelf/edit"},
                {"method": "POST", "path": "/shelf/edit"},
            ]}
            summary = RunSummary(passed=0, total=1, results=[TestOutcome(
                title="Save Shelf", ok=False, status="timedOut", duration_ms=10000,
                message="waiting for updated shelf")])
            digest = flow.failure_diagnostics("REQ-1", summary)
            self.assertIn("POST /shelf/edit", digest)
            self.assertIn("static hint, not a verdict", digest)
            self.assertEqual(flow.failure_diagnostics("REQ-1", RunSummary(error="test loader failed")), "")
            summary.passed = 1
            summary.results[0].ok = True
            self.assertEqual(flow.failure_diagnostics("REQ-1", summary), "")


class InteractionDiagnosticsTests(unittest.TestCase):
    def test_should_add_interaction_hint_without_design_or_extra_acceptance_loop(self):
        import argparse, tempfile
        from pathlib import Path
        from acceptance import RunSummary, TestOutcome
        with tempfile.TemporaryDirectory() as tmp:
            flow = m.Flow(argparse.Namespace(web_port=3000), Path(tmp), Path(tmp))
            summary = RunSummary(results=[TestOutcome(
                title="Undo", ok=False, status="timedOut", duration_ms=10000,
                message="waiting for getByRole('button', { name: /^Undo$/i })")])
            digest = flow.failure_diagnostics("REQ-1", summary)
            self.assertIn("Interaction audit (hypotheses, not verdicts)", digest)
            self.assertIn("aria-label", digest)
            self.assertNotIn("Route wiring audit", digest)


class InteractionPromptTests(unittest.TestCase):
    def test_should_cover_names_initial_state_and_active_edits_in_existing_prompts(self):
        self.assertIn("aria-label on a control overrides its visible text", m.UI_CONTRACT_CORE)
        self.assertIn("resets an unsaved draft", m.UI_CONTRACT_CORE)
        self.assertIn("packaged persistent store", m.UI_CONTRACT_CORE)
        self.assertIn("test's first action", m.UI_CONTRACT_CORE)
        self.assertIn("complete the write before navigating", m.UI_CONTRACT_CORE)
        self.assertIn("exact semantic role/name required by the spec", m.UI_CONTRACT_CORE)
        self.assertIn("status text separate", m.CODEGEN_PROMPT)
        self.assertIn("wait for success before navigation", m.CODEGEN_PROMPT)
        self.assertIn("pre-navigation match", m.CODEGEN_PROMPT)
        self.assertIn("initial test preconditions", m.INLINE_DESIGN_NOTE)
        self.assertIn("save-success navigation", m.INLINE_DESIGN_NOTE)
        self.assertIn("start from the packaged file without deleting it", m.FINAL_CHECK_PROMPT)
        self.assertIn("successful write is observed before navigation", m.FINAL_CHECK_PROMPT)

    def test_post_login_identity_contract_is_conditional_and_not_navbar_only(self):
        from types import SimpleNamespace

        session_prompt = m.Flow.ui_contract(SimpleNamespace(needs_data=False, needs_session=True))
        non_session_prompt = m.Flow.ui_contract(SimpleNamespace(needs_data=False, needs_session=False))
        self.assertIn("immediately after login", session_prompt)
        self.assertIn("semantic welcome heading in authenticated main content", session_prompt)
        self.assertIn("one visible element", session_prompt)
        self.assertNotIn("semantic welcome heading", non_session_prompt)
        self.assertIn("immediately after login", m.CODEGEN_SIZE_FULL)
        self.assertIn("semantic welcome heading in authenticated main content", m.CODEGEN_SIZE_FULL)
        self.assertIn("follow an explicitly required different role/location", m.CODEGEN_SIZE_FULL)
        self.assertNotIn("<span>USERNAME</span>", m.CODEGEN_SIZE_FULL)
        self.assertNotIn("BookStack", session_prompt + m.CODEGEN_SIZE_FULL)


class FullSuiteDocumentPromptTests(unittest.TestCase):
    def test_should_not_send_harness_failure_to_application_repair(self):
        import argparse
        from acceptance import RunSummary
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tests = root / "tests"
            tests.mkdir()
            for name in ("REQ-1.spec.ts", "REQ-2.spec.ts"):
                (tests / name).write_text("// frozen", encoding="utf-8")
            flow = m.Flow(argparse.Namespace(web_port=3000), root, root)
            flow.tests_dir = tests
            flow.runner = object()
            flow.spec_map = {"REQ-1": ["REQ-1.spec.ts"], "REQ-2": ["REQ-2.spec.ts"], None: []}
            flow.test_verdict = {"REQ-1": True, "REQ-2": True}
            flow.run_specs = lambda *_args, **_kwargs: RunSummary(
                error="Playwright harness configuration/load error: snapshots must be a boolean",
                error_kind="harness")
            turns = []
            flow.turn = lambda *_args: turns.append(_args)
            flow.final_acceptance()
            self.assertEqual(turns, [])
            self.assertEqual(flow.test_verdict, {"REQ-1": True, "REQ-2": True})

    def test_should_trace_the_original_full_suite_and_prioritize_document_evidence(self):
        import argparse
        from acceptance import DocumentResponse, RunSummary, TestOutcome
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tests = root / "tests"
            tests.mkdir()
            for name in ("REQ-1.spec.ts", "REQ-2.spec.ts"):
                (tests / name).write_text("// frozen", encoding="utf-8")
            flow = m.Flow(argparse.Namespace(web_port=3000), root, root)
            flow.tests_dir = tests
            flow.runner = object()
            flow.spec_map = {"REQ-1": ["REQ-1.spec.ts"], "REQ-2": ["REQ-2.spec.ts"], None: []}
            failed = TestOutcome(title="Save", ok=False, status="timedOut", duration_ms=10000,
                                 file="REQ-1.spec.ts", message=("waiting for getByRole('heading', "
                                 "{ name: /Created\\s+Entity/i }).first() to be visible"),
                                 document=DocumentResponse("GET", "/<segment>/<segment>", 200, "text/html"))
            calls, prompts = [], []
            def run_specs(specs, **kwargs):
                calls.append((specs, kwargs))
                if len(calls) == 1:
                    return RunSummary(passed=1, total=2, results=[failed, TestOutcome(
                        title="Green", ok=True, status="passed", duration_ms=100, file="REQ-2.spec.ts")])
                return RunSummary(passed=2, total=2, results=[TestOutcome(
                    title="Save", ok=True, status="passed", duration_ms=100, file="REQ-1.spec.ts"),
                    TestOutcome(title="Green", ok=True, status="passed", duration_ms=100,
                                file="REQ-2.spec.ts")])
            flow.run_specs = run_specs
            flow.record_tests = lambda *_args: None
            flow.turn = lambda prompt, *_args: prompts.append(prompt)
            flow.commit = lambda *_args: True
            flow.sources_text = lambda: ""
            flow.corrections_text = lambda: ""
            flow.remaining = lambda: 1000
            with patch.dict(os.environ, {"OCTOS_FINAL_REPAIR_ROUNDS": "1"}):
                flow.final_acceptance()
            self.assertEqual(len(calls), 2)
            self.assertTrue(all(call[1]["trace_failures"] for call in calls))
            self.assertTrue(all(call[1]["grader_like"] for call in calls))
            self.assertLess(prompts[0].index("Document:"), prompts[0].index("Observation:"))
            self.assertIn("rendered only as a link, button, or plain text", prompts[0])
            self.assertIn("first visible candidate once", prompts[0])

class CodegenPromptTests(unittest.TestCase):
    def test_should_format_without_placeholder_errors_and_keep_build_command(self):
        import main as m
        text = m.CODEGEN_PROMPT.format(node_id="REQ-1", description="S", spec="T", port=3000, ports=" P", size_rule="R")
        self.assertIn("do not output them", text)
        self.assertIn("REQ-1", text)


class AlreadyPassingProbeTests(unittest.TestCase):
    def test_should_mark_only_fully_passing_nodes_as_unchanged(self):
        import argparse
        from pathlib import Path
        from types import SimpleNamespace
        flow = m.Flow(argparse.Namespace(web_port=1), Path("."), Path("."))
        flow.spec_map = {"REQ-1": ["a.spec.ts"], "REQ-2": ["b.spec.ts"], "REQ-3": [], None: []}
        results = {"a.spec.ts": SimpleNamespace(error=None, total=2, passed=2, all_passed=True),
                   "b.spec.ts": SimpleNamespace(error=None, total=2, passed=1, all_passed=False)}
        flow.run_specs = lambda specs, **kw: results[specs[0]]
        self.assertEqual(flow.already_passing_nodes(["REQ-1", "REQ-2", "REQ-3"]), {"REQ-1"})


class CodegenManifestTests(unittest.TestCase):
    def test_should_write_missing_manifests_once(self):
        import json, tempfile
        from pathlib import Path
        root = Path(tempfile.mkdtemp())
        self.assertEqual(m.write_codegen_manifests(root), ["frontend/package.json", "backend/package.json"])
        self.assertEqual(m.write_codegen_manifests(root), [])
        fe = json.loads((root / "frontend/package.json").read_text())
        self.assertIn("mkdirSync('dist',{recursive:true})", fe["scripts"]["build"])
        # the build script must run and emit both register.html and extensionless register
        import shutil, subprocess
        node = shutil.which("node") or "/opt/homebrew/opt/node@24/bin/node"
        (root / "frontend/src").mkdir(parents=True)
        (root / "frontend/src/index.html").write_text("i"); (root / "frontend/src/register.html").write_text("r")
        cmd = fe["scripts"]["build"][len("node -e "):].strip('"').replace('\\"', '"')
        subprocess.run([node, "-e", cmd], cwd=root / "frontend", check=True)
        self.assertEqual((root / "frontend/dist/register").read_text(), "r")
        self.assertTrue((root / "frontend/dist/register.html").is_file())
        self.assertFalse((root / "frontend/dist/index").exists())
        be = json.loads((root / "backend/package.json").read_text())
        self.assertEqual(be["scripts"]["start"], "node server.js")
        self.assertEqual(be["type"], "commonjs")


class ExtraPortsBoundTests(unittest.TestCase):
    def test_should_report_unbound_spec_ports_in_grader_like_mode(self):
        import tempfile
        from pathlib import Path
        from acceptance import AppServer
        srv = AppServer(Path(tempfile.mkdtemp()), 3100, lambda s: None, grader_like=True, extra_ports=[3301])
        srv.port = 3100
        err = srv.extra_ports_bound(wait_seconds=0.3)
        self.assertIn("3301", err)
        self.assertIn("ERR_CONNECTION_REFUSED", err)
        srv.extra_ports = []
        self.assertIsNone(srv.extra_ports_bound(wait_seconds=0.1))


class SnapshotSourcesTests(unittest.TestCase):
    def test_should_copy_sources_but_not_node_modules(self):
        import argparse, tempfile
        from pathlib import Path
        root = Path(tempfile.mkdtemp())
        (root / "frontend/src").mkdir(parents=True); (root / "backend/node_modules/x").mkdir(parents=True)
        (root / "frontend/src/index.html").write_text("<p>")
        (root / "backend/server.js").write_text("x")
        (root / "backend/node_modules/x/i.js").write_text("y")
        flow = m.Flow(argparse.Namespace(web_port=1), root, root)
        dest = flow.snapshot_sources("REQ-1", 0)
        self.assertTrue((dest / "frontend/src/index.html").is_file())
        self.assertTrue((dest / "backend/server.js").is_file())
        self.assertFalse((dest / "backend/node_modules").exists())
