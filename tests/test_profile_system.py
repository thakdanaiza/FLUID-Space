from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import profile_store
import numpy as np
from cad_mask import build_cad_masks, polygon_mask
from phase_analysis_core import refine_bubble_boundaries
from run_profile import generate_compatibility_files


class ProfileSystemTests(unittest.TestCase):
    def test_baseline_is_complete_and_contains_imported_bubbles(self) -> None:
        profile = profile_store.load_profile("current_baseline", require_complete=True)
        self.assertEqual(set(profile["interest_zones"]), set(profile_store.ZONES))
        self.assertEqual(set(profile["rois"]), set(profile_store.CHANNELS))
        self.assertGreater(sum(len(profile["bubbles"][name]) for name in profile_store.CHANNELS), 0)

    def test_generated_roi_has_no_manual_islands(self) -> None:
        _, roi_path, analysis_path, cad_path = generate_compatibility_files("current_baseline")
        import json

        roi = json.loads(roi_path.read_text(encoding="utf-8"))
        analysis = json.loads(analysis_path.read_text(encoding="utf-8"))
        self.assertEqual(roi["exclusion_islands"], [])
        self.assertTrue(cad_path.exists())
        self.assertTrue(all(analysis["wet_area_polygons"][name] == [] for name in profile_store.CHANNELS))

    def test_profile_slug_rejects_empty_names(self) -> None:
        with self.assertRaises(ValueError):
            profile_store.slugify(" !!! ")

    def test_bubble_refinement_never_restores_manually_excluded_pixels(self) -> None:
        frame = np.full((80, 120, 3), 128, dtype=np.uint8)
        wet = np.ones((80, 120), dtype=bool)
        exclusion = {
            "id": "CH1-2-BUBBLE-TEST",
            "kind": "bubble",
            "points": [[20, 15], [94, 18], [103, 39], [87, 61], [30, 66], [15, 43]],
        }
        refinement = refine_bubble_boundaries(
            frame,
            wet,
            [exclusion],
            boundary_width=3,
            smooth_radius=3,
        )
        restored = refinement.drawn_mask & ~refinement.proposed_mask
        self.assertEqual(int(restored.sum()), 0)


if __name__ == "__main__":
    unittest.main()
