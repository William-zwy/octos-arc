import unittest

from capability_plan import build_capability_plan, ordered_node_ids


class CapabilityPlanTests(unittest.TestCase):
    def test_groups_nodes_in_stable_high_fanout_order(self):
        plan = build_capability_plan([
            {"id": "REQ-3", "name": "Export CSV"},
            {"id": "REQ-1", "name": "Open editor route"},
            {"id": "REQ-2", "name": "Edit cell and refresh"},
        ])
        self.assertEqual(ordered_node_ids(plan), ["REQ-1", "REQ-2", "REQ-3"])
        self.assertEqual(plan["mode"], "shadow")

    def test_unknown_nodes_remain_in_plan(self):
        plan = build_capability_plan([{"id": "REQ-X", "name": "Unclassified behavior"}])
        self.assertEqual(ordered_node_ids(plan), ["REQ-X"])
        self.assertEqual(plan["capabilities"][0]["name"], "core_mutation")


if __name__ == "__main__":
    unittest.main()
