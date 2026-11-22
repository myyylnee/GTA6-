import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

FILTER_KEYS = {
    "flow_div",
    "strength",
    "occlusion_sensitivity",
    "detect_threshold",
    "low_latency",
    "debug_mode",
}


def load(name):
    return json.loads((ROOT / "profiles" / name).read_text(encoding="utf-8"))


class ProfileTests(unittest.TestCase):
    def test_ten_iterations_are_recorded(self):
        data = load("iterations.json")
        self.assertEqual(len(data), 10)
        self.assertEqual([x["iteration"] for x in data], list(range(1, 11)))

    def test_iterations_have_change_result_decision(self):
        for item in load("iterations.json"):
            self.assertTrue(item["name"], item)
            self.assertTrue(item["change"], item)
            self.assertTrue(item["result"], item)
            self.assertIn(item["decision"], {"继续", "保留", "淘汰", "备用", "采用"})
            self.assertTrue(set(item["change"]) <= FILTER_KEYS, item)

    def test_final_iteration_matches_adopted_profile(self):
        last = load("iterations.json")[-1]
        adopted = load("optimized-30-to-60.json")["filter"]
        self.assertEqual(last["decision"], "采用")
        for key, value in last["change"].items():
            self.assertEqual(adopted[key], value, key)

    def test_final_profile_targets_fast_motion(self):
        data = load("optimized-30-to-60.json")
        f = data["filter"]
        self.assertEqual(f["flow_div"], 2)
        self.assertEqual(f["occlusion_sensitivity"], 0.65)
        self.assertEqual(f["detect_threshold"], 0.10)
        self.assertTrue(f["low_latency"])
        self.assertEqual(set(f), FILTER_KEYS)

    def test_fallback_profile_only_lowers_flow_resolution(self):
        main = load("optimized-30-to-60.json")
        fallback = load("fallback-low-gpu.json")
        self.assertEqual(fallback["filter"]["flow_div"], 4)
        self.assertEqual(main["fallback"]["flow_div"], fallback["filter"]["flow_div"])
        for key in FILTER_KEYS - {"flow_div"}:
            self.assertEqual(fallback["filter"][key], main["filter"][key], key)

    def test_filter_example_matches_adopted_profile(self):
        example = json.loads(
            (ROOT / "config/filter-settings.example.json").read_text(encoding="utf-8")
        )
        self.assertEqual(example["settings"], load("optimized-30-to-60.json")["filter"])


if __name__ == "__main__":
    unittest.main()
