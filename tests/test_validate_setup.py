import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ValidateSetupTests(unittest.TestCase):
    def make_fixture(self, good=True):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root / "basic/profiles/未命名").mkdir(parents=True)
        (root / "basic/scenes").mkdir(parents=True)
        (root / "plugin_manager").mkdir()
        (root / "basic/profiles/未命名/basic.ini").write_text(
            "[Video]\nBaseCX=1920\nBaseCY=1080\nOutputCX=1920\nOutputCY=1080\nFPSCommon=60\n",
            encoding="utf-8",
        )
        settings = {"flow_div": 2 if good else 4, "strength": 1.0, "occlusion_sensitivity": 0.65, "detect_threshold": 0.10, "low_latency": True, "debug_mode": 0}
        scene = {"sources": [{"name": "视频采集设备", "id": "macos-avcapture", "settings": {"preset": "AVCaptureSessionPreset1920x1080"}, "filters": [{"id": "optical_flow_interpolation_filter", "settings": settings}]}]}
        (root / "basic/scenes/scene.json").write_text(json.dumps(scene, ensure_ascii=False), encoding="utf-8")
        (root / "plugin_manager/modules.json").write_text(json.dumps([{"module_name": "obs-optical-flow", "enabled": True}]), encoding="utf-8")
        return td, root

    def run_validator(self, root):
        return subprocess.run([sys.executable, str(ROOT / "scripts/validate_setup.py"), "--obs-root", str(root)], capture_output=True, text=True)

    def test_good_fixture_passes(self):
        td, root = self.make_fixture(True)
        self.addCleanup(td.cleanup)
        self.assertEqual(self.run_validator(root).returncode, 0)

    def test_bad_filter_is_rejected(self):
        td, root = self.make_fixture(False)
        self.addCleanup(td.cleanup)
        self.assertNotEqual(self.run_validator(root).returncode, 0)


if __name__ == "__main__":
    unittest.main()
