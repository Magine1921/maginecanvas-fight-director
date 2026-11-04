import copy
import json
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from build_node_plan import make_plan, validate_plan, PlanError

BRIEF = Path(__file__).resolve().parents[1] / "examples/brief-rainy-bridge.json"
PLAN = Path(__file__).resolve().parents[1] / "examples/plan-rainy-bridge.json"

class NodePlanTests(unittest.TestCase):
    def setUp(self):
        self.brief = json.loads(BRIEF.read_text(encoding="utf-8"))
        self.plan = make_plan(self.brief)
    def test_valid_example(self):
        validate_plan(self.plan)
        validate_plan(json.loads(PLAN.read_text(encoding="utf-8")))
    def test_deterministic(self):
        self.assertEqual(self.plan, make_plan(self.brief))
    def test_wrong_total_duration(self):
        b = copy.deepcopy(self.brief)
        b["duration_seconds"] += 1
        with self.assertRaises(PlanError): make_plan(b)
    def test_non_decisecond_duration(self):
        b = copy.deepcopy(self.brief)
        b["beats"][0]["duration_seconds"] = 1.25
        with self.assertRaises(PlanError): make_plan(b)
    def test_edit_changes_duration(self):
        b = copy.deepcopy(self.brief)
        b["beats"][0]["duration_seconds"] += 1
        b["duration_seconds"] += 1
        p = make_plan(b)
        self.assertEqual(p["shots"][-1]["time"]["end_sec"], b["duration_seconds"])
    def test_unknown_dependency(self):
        p = copy.deepcopy(self.plan)
        p["workflow"]["nodes"][0]["dependencies"].append("MISSING")
        with self.assertRaises(PlanError): validate_plan(p)
    def test_cycle(self):
        p = copy.deepcopy(self.plan)
        p["workflow"]["nodes"][0]["dependencies"] = ["EDIT-1"]
        with self.assertRaises(PlanError): validate_plan(p)

if __name__ == "__main__":
    unittest.main()
