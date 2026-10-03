import json
import unittest

from requirement_contract import compact_contract, compile_requirement_contract, shared_surface_contract


def tree(*nodes, name="Synthetic App"):
    return {"id": "ROOT", "name": name, "type": "FOLDER", "description": "A reloadable app.",
            "children": list(nodes)}


def node(node_id, description, scenarios):
    return {"id": node_id, "type": "ATOMIC", "name": node_id, "description": description,
            "dependencies": [], "scenarios": scenarios}


class RequirementContractTests(unittest.TestCase):
    def test_compiles_steps_fixtures_and_evidence_without_inventing_locators(self):
        contract = compile_requirement_contract(tree(node(
            "REQ-1", "The current account can reopen the target record after reload.", [{
                "name": "Update record",
                "steps": [
                    {"keyword": "GIVEN", "content": "User is signed in with account `demo@example.com`."},
                    {"keyword": "WHEN", "content": "Click the `Save` button for the selected record."},
                    {"keyword": "THEN", "content": "The record remains saved after reload."},
                ],
            }]
        )))
        item = contract["nodes"][0]
        self.assertEqual(contract["atomic_count"], 1)
        self.assertEqual(contract["scenario_count"], 1)
        self.assertIn("demo@example.com", item["scenarios"][0]["facts"]["exact_values"])
        self.assertIn("Save", item["scenarios"][0]["facts"]["exact_values"])
        self.assertEqual(item["scenarios"][0]["facts"]["actions"], ["Click the `Save` button for the selected record."])
        self.assertTrue(item["scenarios"][0]["facts"]["persistence_hints"])
        self.assertIn("evidence", item["scenarios"][0]["steps"][0])
        self.assertEqual(item["facts"]["paths"], [])
        self.assertIn("refresh_reopen_result", item["acceptance_contract"])
        self.assertTrue(contract["capabilities"])
        self.assertTrue(any(item["kind"] == "refresh_reopen" for item in contract["invariants"]))

    def test_generic_quoted_prose_is_not_executable_fixture(self):
        from requirement_contract import _facts
        facts = _facts("Click 2Q3 Sales2 and follow the requested workflow.")
        facts = _facts('Click "Q3 Sales" and follow "the requested workflow".')
        self.assertIn("the requested workflow", facts["rejected_exact_values"])

    def test_compact_contract_is_valid_json_and_bounded(self):
        contract = compile_requirement_contract(tree(*[
            node(f"REQ-{i}", "x" * 600, [{"name": "s", "steps": [{"keyword": "THEN", "content": "y" * 500}]}])
            for i in range(10)
        ]))
        text = compact_contract(contract, max_chars=900)
        self.assertLessEqual(len(text), 900)
        self.assertTrue(json.loads(text))
        node_text = compact_contract(contract, node_id="REQ-1", max_chars=700)
        self.assertLessEqual(len(node_text), 700)
        self.assertTrue(json.loads(node_text))

    def test_empty_folder_is_not_falsely_counted_as_atomic(self):
        contract = compile_requirement_contract(tree({"id": "FOLDER", "type": "FOLDER", "children": []}))
        self.assertEqual(contract["atomic_count"], 0)

    def test_global_summary_keeps_large_tree_identity_within_prompt_budget(self):
        contract = compile_requirement_contract(tree(*[
            node(f"REQ-{i}", "description", [{"name": "s", "steps": []}])
            for i in range(47)
        ]))
        text = compact_contract(contract, max_chars=7000)
        payload = json.loads(text)
        self.assertEqual(payload["atomic_count"], 47)
        self.assertIn("REQ-0", text)
        self.assertIn("REQ-46", text)

    def test_capability_map_groups_by_first_real_folder(self):
        contract = compile_requirement_contract(tree(
            {"id": "CAP-A", "type": "FOLDER", "children": [node("A-1", "a", []), node("A-2", "a", [])]},
            {"id": "CAP-B", "type": "FOLDER", "children": [node("B-1", "b", [])]},
        ))
        self.assertEqual({item["id"] for item in contract["capabilities"]}, {"CAP-A", "CAP-B"})

    def test_shared_surface_contract_derives_entries_without_domain_literals(self):
        contract = compile_requirement_contract(tree(node(
            "REQ-1", "Open the public workspace.", [{
                "name": "Create workspace",
                "steps": [
                    {"keyword": "GIVEN", "content": "The public page is open."},
                    {"keyword": "WHEN", "content": "Click the `Create workspace` button."},
                    {"keyword": "THEN", "content": "The workspace is visible."},
                ],
            }]
        )))
        surface = shared_surface_contract(contract)
        self.assertEqual(surface["route"], "/")
        self.assertEqual(surface["entries"][0]["name"], "Create workspace")
        self.assertEqual(surface["entries"][0]["role"], "button")
        self.assertEqual(surface["entries"][0]["action"], "Click the `Create workspace` button.")
        self.assertEqual(surface["fanout"]["Create workspace"], 1)

    def test_shared_surface_ignores_fixtures_and_results(self):
        contract = compile_requirement_contract(tree(node(
            "REQ-1", "A public app with authentication and navigation.", [{
                "name": "Open workspace",
                "steps": [
                    {"keyword": "GIVEN", "content": "Use `nora-demo`, `nora.demo@example.test`, and `Valid-password-123!`."},
                    {"keyword": "WHEN", "content": "Click the `Sign in` link, then open the `Acme Demo` navigation target."},
                    {"keyword": "THEN", "content": "The `Acme Demo` navigation displays `East/1200/Open` and range `A1:C6`."},
                ],
            }]
        )))
        surface = shared_surface_contract(contract)
        self.assertEqual(surface["names"], ["Sign in", "Acme Demo"])
        self.assertNotIn("navigation", surface["names"])
        self.assertNotIn("East/1200/Open", surface["names"])
        self.assertNotIn("A1:C6", surface["names"])
        self.assertNotIn("nora-demo", surface["names"])
        self.assertNotIn("nora.demo@example.test", surface["names"])
        self.assertNotIn("Valid-password-123!", surface["names"])

    def test_shared_surface_keeps_short_named_tabs_and_actions(self):
        contract = compile_requirement_contract(tree(node(
            "REQ-1", "Spreadsheet entry actions.", [{
                "name": "Workbook actions",
                "steps": [{
                    "keyword": "WHEN",
                    "content": "Select the `Sheet1` tab, then click the `Create` button and open the `Import CSV` dialog.",
                }],
            }]
        )))
        surface = shared_surface_contract(contract)
        self.assertEqual(surface["names"], ["Sheet1", "Create", "Import CSV"])
        self.assertEqual([entry["role"] for entry in surface["entries"]], ["tab", "button", "dialog"])

    def test_shared_surface_excludes_input_fixtures_and_prefers_ui_route(self):
        contract = compile_requirement_contract(tree(node(
            "REQ-1", "Authentication entry.", [{
                "name": "Sign in",
                "steps": [{
                    "keyword": "WHEN",
                    "content": "Open `/api/session`, visit `/login`, fill `nora-demo` in the username textbox, then click the `Sign in` button.",
                }],
            }]
        )))
        surface = shared_surface_contract(contract)
        self.assertEqual(surface["route"], "/login")
        self.assertEqual(surface["names"], ["Sign in"])

    def test_shared_surface_does_not_assign_later_input_role_to_entry(self):
        contract = compile_requirement_contract(tree(node(
            "REQ-1", "Authentication entry.", [{
                "name": "Sign in",
                "steps": [{
                    "keyword": "WHEN",
                    "content": "Click `Sign in`, then enter `nora-demo` in the username textbox.",
                }],
            }]
        )))
        surface = shared_surface_contract(contract)
        self.assertEqual(surface["names"], ["Sign in"])
        self.assertIsNone(surface["entries"][0]["role"])

    def test_shared_surface_does_not_fallback_to_mixed_role_name_values(self):
        contract = compile_requirement_contract(tree(node(
            "REQ-1", "No structured interaction steps.", []
        )))
        contract["nodes"][0]["acceptance_contract"]["role_name"] = ["navigation", "1200", "Seed workbook"]
        surface = shared_surface_contract(contract)
        self.assertEqual(surface["names"], [])
        self.assertEqual(surface["confidence"], "unknown")


if __name__ == "__main__":
    unittest.main()
