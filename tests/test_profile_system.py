from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import profile_store
from phase_analysis_core import refine_bubble_boundaries
from run_profile import command_for_profile


class ProfileSystemTests(unittest.TestCase):
    def test_v1_baseline_is_exposed_as_four_single_setup_profiles(self) -> None:
        names = profile_store.list_profiles()
        expected = {f"current_baseline_{channel}" for channel in profile_store.LEGACY_CHANNELS}
        self.assertTrue(expected.issubset(names))
        for name in expected:
            profile = profile_store.load_profile(name, require_complete=True)
            self.assertEqual(profile["schema_version"], 2)
            self.assertTrue(profile["cad"]["enabled"])
            self.assertGreaterEqual(len(profile["geometry"]["analysis_roi"]), 3)
            self.assertGreaterEqual(len(profile["geometry"]["calibration_roi"]), 3)

    def test_profile_dimensions_are_not_fixed_to_legacy_video_size(self) -> None:
        profile = profile_store.load_profile("current_baseline_CH1-1")
        custom = copy.deepcopy(profile)
        custom["name"] = "custom_dimensions"
        custom["frame"].update({"width": 1920, "height": 1080})
        custom["geometry"] = {
            "interest_zone": [[0, 0], [1919, 0], [1919, 1079], [0, 1079]],
            "analysis_roi": [[10, 10], [1000, 10], [1000, 500], [10, 500]],
            "calibration_roi": [[20, 20], [80, 20], [80, 80], [20, 80]],
            "bubbles": [],
        }
        custom["cad"] = {"enabled": False}
        validated = profile_store.validate_profile(custom, require_complete=True)
        self.assertEqual((validated["frame"]["width"], validated["frame"]["height"]), (1920, 1080))

    def test_runner_uses_single_profile_pipeline(self) -> None:
        command = command_for_profile("current_baseline_CH1-1", check=True)
        self.assertTrue(command[1].endswith("single_profile_pipeline.py"))
        self.assertEqual(command[command.index("--profile") + 1], "current_baseline_CH1-1")
        self.assertIn("--check", command)

    def test_profile_slug_rejects_empty_names(self) -> None:
        with self.assertRaises(ValueError):
            profile_store.slugify(" !!! ")

    def test_bubble_refinement_never_restores_manually_excluded_pixels(self) -> None:
        frame = np.full((80, 120, 3), 128, dtype=np.uint8)
        wet = np.ones((80, 120), dtype=bool)
        exclusion = {
            "id": "BUBBLE-TEST",
            "kind": "bubble",
            "points": [[20, 15], [94, 18], [103, 39], [87, 61], [30, 66], [15, 43]],
        }
        refinement = refine_bubble_boundaries(frame, wet, [exclusion], boundary_width=3, smooth_radius=3)
        restored = refinement.drawn_mask & ~refinement.proposed_mask
        self.assertEqual(int(restored.sum()), 0)


if __name__ == "__main__":
    unittest.main()
