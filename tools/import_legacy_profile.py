from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from profile_store import CHANNELS, save_profile


def main() -> None:
    roi = json.loads((ROOT / "tools" / "legacy.roi.json").read_text(encoding="utf-8"))
    phase = json.loads((ROOT / "tools" / "legacy.phase_v2.json").read_text(encoding="utf-8"))
    frame_index = int(roi["source"]["frame_index"])
    raw_bubbles = phase.get("frame_exclusions", {}).get(str(frame_index), {})
    profile = {
        "schema_version": 1,
        "name": "current_baseline",
        "description": "Baseline imported from the approved CAD-authoritative setup.",
        "frame": {"index": frame_index, "width": 1090, "height": 340},
        "fixed_assets": {
            "video": "assets/reference.mp4",
            "cad_outline": "assets/cad_pair_lines.npz",
            "cad_vectors": "assets/cad_pair_vector_lines.json",
            "cad_placement": "assets/cad_placement.json",
        },
        "interest_zones": {name: roi["zones"][name] for name in ("ZONE-CH1", "ZONE-CH2")},
        "rois": {channel: roi["rois"][channel] for channel in CHANNELS},
        "calibration_rois": {name: roi["calibration_rois"][name] for name in ("CAL-CH1", "CAL-CH2")},
        "bubbles": {
            channel: [
                {"id": item["id"], "points": item["points"]}
                for item in raw_bubbles.get(channel, [])
                if item.get("kind") == "bubble"
            ]
            for channel in CHANNELS
        },
        "settings": {"bubble_smooth_radius": 3, "equalize_cad_lengths": True},
    }
    print(save_profile(profile, require_complete=True))


if __name__ == "__main__":
    main()
