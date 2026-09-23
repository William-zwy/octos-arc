import json
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from acceptance import (
    failure_summaries,
    DocumentResponse,
    document_from_trace,
    interaction_failure_hints,
    RunSummary,
    TestOutcome,
    isolated_install_env,
    map_specs_to_nodes,
    playwright_version_hint,
    nodes_for_failures,
    restore_tree,
    restore_worktree,
    robustness_probe,
    route_contract_gaps,
    workers_for_memory,
    snapshot_worktree,
    tree_digest,
    spec_node_id,
    summarize_report,
    AcceptanceRunner,
    playwright_harness_error,
)


class SpecIdTests(unittest.TestCase):
    def test_should_extract_leading_requirement_id(self):
        self.assertEqual(spec_node_id("REQ-1.spec.ts"), "REQ-1")
        self.assertEqual(spec_node_id("REQ-1.1-user-registration.spec.ts"), "REQ-1.1")
        self.assertEqual(spec_node_id("sub/REQ-12.3.4-x.spec.ts"), "REQ-12.3.4")
        self.assertIsNone(spec_node_id("support/e2e.ts"))
        self.assertIsNone(spec_node_id("smoke.spec.ts"))


class MappingTests(unittest.TestCase):
    def test_should_match_exact_ids(self):
        mapping, aliases = map_specs_to_nodes(["REQ-1.spec.ts", "REQ-2.spec.ts"], ["REQ-1", "REQ-2"])
        self.assertEqual(mapping, {"REQ-1": ["REQ-1.spec.ts"], "REQ-2": ["REQ-2.spec.ts"], None: []})
        self.assertEqual(aliases, {})

    def test_should_map_in_order_when_spec_ids_differ_but_counts_match(self):
        specs = ["REQ-1.1-user-registration.spec.ts", "REQ-1.2-user-login.spec.ts", "support/e2e.ts"]
        mapping, aliases = map_specs_to_nodes(specs, ["REQ-1", "REQ-2"])
        self.assertEqual(mapping["REQ-1"], ["REQ-1.1-user-registration.spec.ts"])
        self.assertEqual(mapping["REQ-2"], ["REQ-1.2-user-login.spec.ts"])
        self.assertEqual(aliases, {"REQ-1.1": "REQ-1", "REQ-1.2": "REQ-2"})

    def test_should_fall_back_to_parent_prefix_and_leave_rest_unassigned(self):
        specs = ["REQ-1.1-a.spec.ts", "REQ-1.2-b.spec.ts", "REQ-9.spec.ts"]
        mapping, aliases = map_specs_to_nodes(specs, ["REQ-1", "REQ-2"])
        self.assertEqual(mapping["REQ-1"], ["REQ-1.1-a.spec.ts", "REQ-1.2-b.spec.ts"])
        self.assertEqual(mapping["REQ-2"], [])
        self.assertEqual(mapping[None], ["REQ-9.spec.ts"])
        self.assertEqual(aliases, {"REQ-1.1": "REQ-1", "REQ-1.2": "REQ-1"})

    def test_should_sort_spec_ids_numerically_when_mapping_in_order(self):
        specs = ["REQ-1.10-x.spec.ts", "REQ-1.2-y.spec.ts"]
        mapping, _ = map_specs_to_nodes(specs, ["A", "B"])
        self.assertEqual(mapping["A"], ["REQ-1.2-y.spec.ts"])
        self.assertEqual(mapping["B"], ["REQ-1.10-x.spec.ts"])


def report(*tests):
    specs = []
    for title, status, error, steps, duration in tests:
        result = {"status": status, "duration": duration, "steps": [{"title": s, "category": "pw:api"} for s in steps]}
        if error:
            result["error"] = {"message": error, "location": {"file": "/w/tests/REQ-1.spec.ts", "line": 12}}
            result["errors"] = [result["error"]]
        specs.append({"title": title, "file": "REQ-1.spec.ts", "tests": [{"status": "expected" if status == "passed" else "unexpected", "results": [result]}]})
    return {"suites": [{"title": "REQ-1.spec.ts", "specs": specs}]}


class ReportTests(unittest.TestCase):
    def test_should_count_passed_and_collect_durations(self):
        summary = summarize_report(report(("a", "passed", None, [], 800), ("b", "failed", "boom", [], 10500)))
        self.assertEqual((summary.passed, summary.total), (1, 2))
        self.assertEqual([r.title for r in summary.results if not r.ok], ["b"])
        self.assertEqual(summary.slow(3000), ["b"])

    def test_should_treat_missing_report_as_zero_of_zero(self):
        summary = summarize_report({})
        self.assertEqual((summary.passed, summary.total), (0, 0))

    def test_should_build_four_field_summary_without_ansi_and_with_last_steps(self):
        msg = "\x1b[31mError: expect(locator).toHaveText(expected)\x1b[39m\n\nLocator: getByTestId('count')\nExpected string: \"2\"\nReceived string: \"1\""
        steps = ["page.goto(/)", "locator.click", "locator.click", "expect.toHaveText"]
        summary = summarize_report(report(("REQ-1: increments", "failed", msg, steps, 5000)))
        text = failure_summaries(summary, max_steps=3)
        self.assertIn("Feature: REQ-1: increments", text)
        self.assertIn("Failed at: REQ-1.spec.ts:12", text)
        self.assertIn("Observation: Error: expect(locator).toHaveText(expected)", text)
        self.assertNotIn("\x1b", text)
        self.assertIn("Steps: locator.click -> locator.click -> expect.toHaveText", text)

    def test_should_use_call_log_lines_when_no_step_trace(self):
        msg = "Error: page.goto: net::ERR_CONNECTION_REFUSED\nCall log:\n  - navigating to \"http://x/\", waiting until \"load\"\n\nmore"
        summary = summarize_report(report(("t", "failed", msg, [], 100)))
        self.assertIn('Steps: navigating to "http://x/", waiting until "load"', failure_summaries(summary))

    def test_should_report_timeouts_without_assigning_a_cause(self):
        summary = summarize_report(report(("slow one", "timedOut", "Test timeout of 10000ms exceeded.", ["page.reload"], 10000)))
        text = failure_summaries(summary)
        self.assertIn("timed out", text.lower())
        self.assertIn("cause not established", text)
        self.assertNotIn("request never settled", text)

    def test_should_offer_bounded_interaction_hypotheses_from_failure_evidence(self):
        summary = summarize_report(report(
            ("undo", "timedOut", "waiting for getByRole('button', { name: /^Undo$/i })", [], 10000),
            ("edit", "failed", "getByRole('button', { name: 'Save' }): element was detached from the DOM", [], 10000),
            ("archive", "timedOut", "locator.hover: waiting for getByText('Travel plans')", [], 10000),
        ))
        hints = interaction_failure_hints(summary)
        self.assertEqual(len(hints), 3)
        self.assertIn("aria-label", hints[0])
        self.assertIn("re-renders", hints[1])
        self.assertIn("packaged data", hints[2])
        self.assertEqual(len(interaction_failure_hints(summary, max_hints=2)), 2)
        self.assertEqual(interaction_failure_hints(RunSummary(results=[])), [])
        self.assertEqual(interaction_failure_hints(summarize_report(report(
            ("route", "timedOut", "Test timeout of 10000ms exceeded.", [], 10000),
        ))), [])

    def test_should_hint_at_async_result_role_selected_before_navigation(self):
        summary = summarize_report(report((
            "Save book",
            "timedOut",
            "waiting for getByRole('heading', { name: 'Book Created' }).toBeVisible()",
            ["locator.click", "page.goto"],
            10000,
        )))
        hints = interaction_failure_hints(summary)
        hint_text = " ".join(hints)
        self.assertIn("Post-save result", hint_text)
        self.assertIn("before navigation", hint_text)
        self.assertIn("exact tested role/name", hint_text)

    def test_should_route_exact_final_failure_signatures_without_cross_talk(self):
        entity = TestOutcome(
            title="Save entity", ok=False, status="timedOut", duration_ms=10013,
            message="waiting for getByRole('heading', { name: /Page\\s+Created\\s+6\\.1\\.1/i }).first() to be visible",
            steps=["locator.click", "expect.toBeVisible"],
            document=DocumentResponse("GET", "/<segment>/<segment>", 200, "text/html"),
        )
        state = TestOutcome(
            title="Toggle state", ok=False, status="timedOut", duration_ms=10015,
            message="waiting for getByRole('heading', { name: /^Unfavorite$/i }).first() to be visible",
            steps=["locator.click", "expect.toBeVisible"],
            document=DocumentResponse("GET", "/<segment>/<segment>", 200, "text/html"),
        )
        navigation = TestOutcome(
            title="Quick navigation", ok=False, status="failed", duration_ms=1322,
            message="Error: page.goto: net::ERR_ABORTED at http://127.0.0.1:3000/",
            steps=["page.goto"],
        )
        entity_hint = " ".join(interaction_failure_hints(RunSummary(results=[entity])))
        state_hint = " ".join(interaction_failure_hints(RunSummary(results=[state])))
        navigation_hint = " ".join(interaction_failure_hints(RunSummary(results=[navigation])))
        self.assertIn("rendered only as a link, button, or plain text", entity_hint)
        self.assertIn("first visible candidate once", entity_hint)
        self.assertNotIn("roll back", entity_hint)
        self.assertNotIn("native form", entity_hint)
        self.assertIn("publish the new state immediately", state_hint)
        self.assertIn("roll back on failure", state_hint)
        self.assertNotIn("rendered only as a link", state_hint)
        self.assertNotIn("native form", state_hint)
        self.assertIn("async fetch completion assigns window.location", navigation_hint)
        self.assertIn("native form with a 303", navigation_hint)
        self.assertIn("do not mask the race with a longer timeout", navigation_hint)
        self.assertNotIn("visible heading", navigation_hint)

    def test_should_not_add_final_signature_hints_to_ordinary_failures(self):
        ordinary = TestOutcome(
            title="Validation", ok=False, status="failed", duration_ms=100,
            message="expect(received).toEqual(expected)", steps=["expect.toEqual"],
            document=DocumentResponse("GET", "/<segment>", 200, "text/html"),
        )
        self.assertEqual(interaction_failure_hints(RunSummary(results=[ordinary])), [])


class DocumentTraceTests(unittest.TestCase):
    @staticmethod
    def trace(path, final_url, network, version="1.63.0"):
        trace = [
            {"type": "context-options", "playwrightVersion": version},
            {"type": "frame-snapshot", "snapshot": {"isMainFrame": True, "pageId": "p", "frameId": "f",
                                                    "frameUrl": final_url}},
        ]
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr("trace.trace", "\n".join(json.dumps(x) for x in trace))
            archive.writestr("trace.network", "\n".join(json.dumps(x) for x in network))

    @staticmethod
    def event(url, status, kind="document", method="GET", stamp=1, mime="text/html"):
        return {"type": "resource-snapshot", "snapshot": {
            "pageref": "p", "_frameref": "f", "_resourceType": kind, "_monotonicTime": stamp,
            "request": {"method": method, "url": url, "headers": [{"value": "cookie-secret"}],
                        "postData": {"text": "body-secret"}},
            "response": {"status": status, "content": {"mimeType": mime, "text": "response-secret"}},
        }}

    def test_should_put_verified_main_document_before_locator_and_redact_secrets(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            url = "http://localhost:3100/books/b8/pages/%7B%7BPAGE_ACTION%7D%7D?token=query-secret#fragment-secret"
            self.trace(root / "trace.zip", url, [self.event(url, 404, method="POST", mime="application/json")])
            self.assertEqual(document_from_trace(root / "trace.zip").path,
                             "/<segment>/<segment>/<segment>/<unexpanded-placeholder>")
            raw = report(("Save Page", "timedOut", "waiting for getByRole('heading')", [], 10000))
            raw["suites"][0]["specs"][0]["tests"][0]["results"][0]["attachments"] = [
                {"name": "trace", "path": "trace.zip", "contentType": "application/zip"}]
            digest = failure_summaries(summarize_report(raw, trace_root=root))
            self.assertLess(digest.index("Document:"), digest.index("Observation:"))
            self.assertIn("POST /<segment>/<segment>/<segment>/<unexpanded-placeholder> -> 404 application/json", digest)
            self.assertIn("Transport-first check", digest)
            for secret in ("query-secret", "fragment-secret", "cookie-secret", "body-secret", "response-secret"):
                self.assertNotIn(secret, digest)

    def test_should_redact_pure_letter_usernames_and_path_slugs(self):
        with tempfile.TemporaryDirectory() as tmp:
            url = "http://localhost/users/alice/projects/private?key=query-secret"
            path = Path(tmp) / "trace.zip"
            self.trace(path, url, [self.event(url, 404, mime="application/json")])
            document = document_from_trace(path)
            self.assertEqual(document.path, "/<segment>/<segment>/<segment>/<segment>")
            for secret in ("alice", "private", "query-secret", "users"):
                self.assertNotIn(secret, document.path)

    def test_should_ignore_later_subresource_404_and_final_redirect_200(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "trace.zip"
            final_url = "http://localhost/books/b8"
            self.trace(path, final_url, [
                self.event("http://localhost/books/b8/pages", 302, method="POST", stamp=1),
                self.event(final_url, 200, stamp=2),
                self.event("http://localhost/favicon.ico", 404, kind="image", stamp=3),
            ])
            document = document_from_trace(path)
            self.assertEqual((document.status, document.content_type), (200, "text/html"))
            self.assertFalse(document.suspicious)

    def test_should_abstain_when_trace_missing_untrusted_or_not_reproduced(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "trace.zip"
            self.assertIsNone(document_from_trace(path))
            url = "http://localhost/doc"
            self.trace(path, url, [self.event(url, 404)], version="1.99.0")
            self.assertIsNone(document_from_trace(path))
            self.trace(path, "http://localhost/other", [self.event(url, 404)])
            self.assertIsNone(document_from_trace(path))
            raw = report(("green", "passed", None, [], 100))
            raw["suites"][0]["specs"][0]["tests"][0]["results"][0]["attachments"] = [
                {"name": "trace", "path": "trace.zip"}]
            self.assertIsNone(summarize_report(raw, trace_root=root).results[0].document)
            raw = report(("failed", "timedOut", "waiting for getByRole('button')", [], 10000))
            self.assertNotIn("Document:", failure_summaries(summarize_report(raw, trace_root=root)))

    def test_should_abstain_when_multiple_pages_have_document_responses(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "trace.zip"
            first = "http://localhost/one"
            second = "http://localhost/two"
            frames = [
                {"type": "context-options", "playwrightVersion": "1.63.0"},
                {"type": "frame-snapshot", "snapshot": {"isMainFrame": True, "pageId": "p", "frameId": "f", "frameUrl": first}},
                {"type": "frame-snapshot", "snapshot": {"isMainFrame": True, "pageId": "q", "frameId": "g", "frameUrl": second}},
            ]
            other = self.event(second, 404, stamp=2)
            other["snapshot"].update({"pageref": "q", "_frameref": "g"})
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("trace.trace", "\n".join(json.dumps(x) for x in frames))
                archive.writestr("trace.network", "\n".join(json.dumps(x) for x in [self.event(first, 200), other]))
            self.assertIsNone(document_from_trace(path))

    def test_should_enable_trace_only_when_requested(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tests = root / "tests"
            tests.mkdir()
            (tests / "REQ-1.spec.ts").write_text("// frozen", encoding="utf-8")
            runner = AcceptanceRunner(root, tests, root / "work", lambda _message: None)
            plain = runner._prepare().read_text()
            traced = runner._prepare(trace_failures=True).read_text()
            self.assertNotIn("retain-on-failure", plain)
            self.assertIn("retain-on-failure", traced)
            self.assertIn("snapshots: true", traced)
            self.assertNotIn("snapshots: {", traced)
            self.assertEqual((runner.work_dir / "tests/REQ-1.spec.ts").read_text(), "// frozen")

    def test_should_extract_from_same_run_attachment_then_discard_raw_trace(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tests = root / "tests"
            tests.mkdir()
            (tests / "REQ-1.spec.ts").write_text("// frozen", encoding="utf-8")
            runner = AcceptanceRunner(root, tests, root / "work", lambda _message: None)
            url = "http://localhost/doc"
            raw = report(("failed", "timedOut", "waiting for getByRole('heading')", [], 10000))
            raw["suites"][0]["specs"][0]["tests"][0]["results"][0]["attachments"] = [
                {"name": "trace", "path": "test-results/case/trace.zip"}]

            def fake_run(*_args, **_kwargs):
                trace_dir = runner.work_dir / "test-results/case"
                trace_dir.mkdir(parents=True)
                self.trace(trace_dir / "trace.zip", url, [self.event(url, 404, mime="application/json")])
                (runner.work_dir / "report.json").write_text(json.dumps(raw), encoding="utf-8")
                return SimpleNamespace(returncode=1, stdout="", stderr="")

            with patch("acceptance.subprocess.run", side_effect=fake_run):
                summary = runner.run(["REQ-1.spec.ts"], "http://localhost", trace_failures=True)
            self.assertEqual(summary.results[0].document.status, 404)
            self.assertFalse((runner.work_dir / "test-results").exists())

    def test_should_classify_only_runner_wide_playwright_config_errors(self):
        broken = RunSummary(total=2, results=[
            TestOutcome(title="A", ok=False, status="failed", duration_ms=0,
                        message="config.use.trace.snapshots must be a boolean"),
            TestOutcome(title="B", ok=False, status="failed", duration_ms=0,
                        message="config.use.trace.snapshots must be a boolean"),
        ])
        self.assertIn("snapshots", playwright_harness_error(broken))
        mixed = RunSummary(total=2, results=[broken.results[0], TestOutcome(
            title="B", ok=False, status="failed", duration_ms=0,
            message="expected heading to be visible")])
        self.assertIsNone(playwright_harness_error(mixed))
        app = RunSummary(total=1, results=[TestOutcome(
            title="A", ok=False, status="failed", duration_ms=0,
            message="playwright.config text rendered in the page")])
        self.assertIsNone(playwright_harness_error(app))


class RouteContractTests(unittest.TestCase):
    def test_should_hint_at_missing_method_and_dynamic_route_wiring(self):
        design = {"routes": [
            "GET /shelf/:id/edit",
            "POST /shelf/:id/edit",
            {"method": "GET", "path": "/page/:id/delete"},
            {"method": "POST", "path": "/page/:id/delete"},
        ]}
        server = """
            function handleShelfEdit(req, res) {}
            if (/^\\/shelf\\/[^\\/]+\\/edit$/.test(pathname) && req.method === 'GET') {
              serveStatic(req, res, '/shelf_edit');
            }
            if (/^\\/page\\/[^\\/]+\\/edit$/.test(pathname) && req.method === 'GET') {
              serveStatic(req, res, '/page_edit');
            }
            // if (/^\\/page\\/[^\\/]+\\/delete$/.test(pathname) && req.method === 'POST') {
        """
        self.assertEqual(route_contract_gaps(design, server), [
            "POST /shelf/:id/edit", "GET /page/:id/delete", "POST /page/:id/delete",
        ])
        connected = server + """
            if (/^\\/shelf\\/[^\\/]+\\/edit$/.test(pathname) && req.method === 'POST') {}
            if (/^\\/page\\/[^\\/]+\\/delete$/.test(pathname) && req.method === 'GET') {}
            if (/^\\/page\\/[^\\/]+\\/delete$/.test(pathname) && req.method === 'POST') {}
        """
        self.assertEqual(route_contract_gaps(design, connected), [])

    def test_should_recognize_literal_routes_and_abstain_on_unknown_router(self):
        design = {"routes": ["GET /shelf/new", "POST /shelf/create",
                             {"method": "GET", "path": "/about"}]}
        server = "if (pathname === '/shelf/new' && req.method === 'GET') {}"
        self.assertEqual(route_contract_gaps(design, server), ["POST /shelf/create"])
        self.assertEqual(route_contract_gaps(design, "router.post('/shelf/create', handler)"), [])
        self.assertEqual(route_contract_gaps(None, server), [])


if __name__ == "__main__":
    unittest.main()


class WorktreeSnapshotTests(unittest.TestCase):
    def test_should_undo_test_run_mutations_but_keep_uncommitted_edits(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run = lambda args: subprocess.run(["git", *args], cwd=root, check=False, capture_output=True,  # noqa: E731
                                              env={"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@x", "GIT_COMMITTER_NAME": "t",
                                                   "GIT_COMMITTER_EMAIL": "t@x", "PATH": "/usr/bin:/bin:/opt/homebrew/bin"})
            run(["init", "-q"])
            (root / "backend").mkdir()
            (root / "backend" / "db.json").write_text('{"count": 0}')
            (root / "backend" / "server.js").write_text("v1")
            run(["add", "-A"]); run(["commit", "-qm", "init"])
            (root / "backend" / "server.js").write_text("v2 (repair edit, uncommitted)")
            snapshot_worktree(run)
            # the test run mutates the store and creates a new file
            (root / "backend" / "db.json").write_text('{"count": -1}')
            (root / "backend" / "uploads.json").write_text("[]")
            restore_worktree(run)
            self.assertEqual((root / "backend" / "db.json").read_text(), '{"count": 0}')
            self.assertEqual((root / "backend" / "server.js").read_text(), "v2 (repair edit, uncommitted)")
            self.assertFalse((root / "backend" / "uploads.json").exists())


class FailureGroupingTests(unittest.TestCase):
    def test_should_group_failed_tests_by_owning_node_via_spec_basename(self):
        summary = summarize_report({"suites": [
            {"title": "a", "file": "REQ-1.spec.ts", "specs": [
                {"title": "one", "file": "REQ-1.spec.ts", "tests": [{"status": "unexpected", "results": [{"status": "failed", "duration": 1,
                    "error": {"message": "x", "location": {"file": "/w/tests/REQ-1.spec.ts", "line": 3}}}]}]}]},
            {"title": "b", "file": "sub/REQ-2.spec.ts", "specs": [
                {"title": "two", "file": "sub/REQ-2.spec.ts", "tests": [{"status": "expected", "results": [{"status": "passed", "duration": 1}]}]},
                {"title": "three", "file": "sub/REQ-2.spec.ts", "tests": [{"status": "unexpected", "results": [{"status": "timedOut", "duration": 1}]}]}]},
        ]})
        grouped = nodes_for_failures(summary.results, {"REQ-1": ["REQ-1.spec.ts"], "REQ-2": ["sub/REQ-2.spec.ts"], None: []})
        self.assertEqual({k: [r.title for r in v] for k, v in grouped.items()}, {"REQ-1": ["one"], "REQ-2": ["three"]})


class PrivateInstallTests(unittest.TestCase):
    def test_should_pin_version_from_tests_package_lock_or_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            tests = Path(tmp) / "tests"; tests.mkdir()
            self.assertEqual(playwright_version_hint(tests, fallback="1.63.0"), "1.63.0")
            (Path(tmp) / "package-lock.json").write_text(
                '{"packages": {"node_modules/@playwright/test": {"version": "1.55.1"}}}')
            self.assertEqual(playwright_version_hint(tests), "1.55.1")
            (tests / "package.json").write_text('{"devDependencies": {"@playwright/test": "^1.52.0"}}')
            self.assertEqual(playwright_version_hint(tests), "1.52.0")

    def test_should_keep_every_write_inside_the_private_root(self):
        env = isolated_install_env(Path("/private/x"))
        for key in ("npm_config_cache", "NPM_CONFIG_CACHE", "PLAYWRIGHT_BROWSERS_PATH"):
            self.assertTrue(env[key].startswith("/private/x"), key)
        self.assertIn("npmmirror", env["PLAYWRIGHT_DOWNLOAD_HOST"])


class ProtectedTreeTests(unittest.TestCase):
    def test_should_restore_changed_deleted_and_added_files(self):
        import shutil
        with tempfile.TemporaryDirectory() as tmp:
            live = Path(tmp) / "tests"; (live / "support").mkdir(parents=True)
            (live / "REQ-1.spec.ts").write_text("original"); (live / "support" / "e2e.ts").write_text("helper")
            snap = Path(tmp) / "snap"; shutil.copytree(live, snap)
            digest = tree_digest(live)
            (live / "REQ-1.spec.ts").write_text("tampered"); (live / "support" / "e2e.ts").unlink()
            (live / "playwright.config.ts").write_text("injected")
            fixed = restore_tree(live, snap, digest)
            self.assertEqual(sorted(fixed), ["REQ-1.spec.ts", "playwright.config.ts", "support/e2e.ts"])
            self.assertEqual((live / "REQ-1.spec.ts").read_text(), "original")
            self.assertEqual((live / "support" / "e2e.ts").read_text(), "helper")
            self.assertFalse((live / "playwright.config.ts").exists())
            self.assertEqual(tree_digest(live), digest)

    def test_should_report_zero_tests_as_load_error(self):
        summary = summarize_report({"suites": [], "errors": [{"message": "SyntaxError: Unexpected token"}]})
        self.assertEqual(summary.total, 0)
        self.assertEqual(summary.load_errors, ["SyntaxError: Unexpected token"])


class HelperLocationTests(unittest.TestCase):
    def test_should_attribute_failure_raised_in_helper_to_the_spec_file(self):
        rep = {"suites": [{"title": "REQ-2.3.1-x.spec.ts", "file": "REQ-2.3.1-x.spec.ts", "specs": [
            {"title": "REQ-2.3.1: trash view", "file": "REQ-2.3.1-x.spec.ts", "tests": [{"status": "unexpected", "results": [
                {"status": "failed", "duration": 900, "error": {"message": "boom", "location": {"file": "/w/tests/support/e2e.ts", "line": 48}}}]}]}]}]}
        summary = summarize_report(rep)
        grouped = nodes_for_failures(summary.results, {"REQ-2.3.1": ["REQ-2.3.1-x.spec.ts"], None: []})
        self.assertEqual(list(grouped), ["REQ-2.3.1"])
        self.assertIn("Failed at: e2e.ts:48 (called from REQ-2.3.1-x.spec.ts)", failure_summaries(summary))


class MemoryWorkersTests(unittest.TestCase):
    def test_should_scale_workers_to_container_memory(self):
        self.assertEqual(workers_for_memory(None, 4), 4)
        self.assertEqual(workers_for_memory(512 * 1024 * 1024, 4), 1)
        self.assertEqual(workers_for_memory(2 * 1024 * 1024 * 1024, 4), 2)
        self.assertEqual(workers_for_memory(8 * 1024 * 1024 * 1024, 4), 4)


class RobustnessProbeTests(unittest.TestCase):
    def test_should_pass_for_a_server_that_answers_404_and_fail_for_a_dead_port(self):
        import http.server, socket, threading
        class H(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(404); self.end_headers()
            def log_message(self, *a): pass
        srv = http.server.HTTPServer(("127.0.0.1", 0), H); port = srv.server_address[1]
        th = threading.Thread(target=srv.serve_forever, daemon=True); th.start()
        try:
            self.assertIsNone(robustness_probe(port, None, timeout=3))
        finally:
            srv.shutdown()
        with socket.socket() as s:
            s.bind(("127.0.0.1", 0)); free = s.getsockname()[1]
        err = robustness_probe(free, None, timeout=2)
        self.assertIn("no HTTP response", err)
