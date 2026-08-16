from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from cad_mask import build_cad_masks
from profile_store import CHANNELS, load_profile, profile_path, project_root


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run one FLUID-Space profile")
    parser.add_argument("--profile", default="current_baseline")
    parser.add_argument("--check", action="store_true")
    return parser.parse_args()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def generate_compatibility_files(profile_name: str) -> tuple[dict[str, Any], Path, Path, Path]:
    root = project_root()
    profile = load_profile(profile_name, require_complete=True)
    profile_dir = profile_path(profile_name).parent
    generated = profile_dir / ".generated"
    generated.mkdir(parents=True, exist_ok=True)
    frame_index = int(profile["frame"]["index"])
    roi_path = generated / "roi.json"
    analysis_path = generated / "analysis.json"
    cad_masks_path = generated / "cad_masks.npz"
    roi_payload = {
        "schema_version": 3,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "source": {
            "video_path": str((root / "assets" / "reference.mp4").resolve()),
            "video_name": "reference.mp4",
            "frame_index": frame_index,
            "frame_time_sec": frame_index / 30.0,
            "frame_width": int(profile["frame"]["width"]),
            "frame_height": int(profile["frame"]["height"]),
            "fps": 30.0,
        },
        "channels": list(CHANNELS),
        "rois": profile["rois"],
        "zones": profile["interest_zones"],
        "calibration_rois": profile["calibration_rois"],
        "exclusion_islands": [],
        "notes": {
            "geometry_policy": "CAD authoritative; ROI and interest zone only remove CAD pixels.",
            "generated_from_profile": profile["name"],
        },
    }
    write_json(roi_path, roi_payload)
    analysis_payload = {
        "schema_version": 1,
        "updated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": {
            "video_path": str((root / "assets" / "reference.mp4").resolve()),
            "video_name": "reference.mp4",
            "reference_frame": frame_index,
            "frame_time_sec": frame_index / 30.0,
            "frame_width": int(profile["frame"]["width"]),
            "frame_height": int(profile["frame"]["height"]),
            "fps": 30.0,
        },
        "roi_project": {"path": str(roi_path.resolve()), "sha256": sha256(roi_path)},
        "wet_area_polygons": {channel: [] for channel in CHANNELS},
        "frame_exclusions": {
            str(frame_index): {
                channel: [
                    {"id": item["id"], "kind": "bubble", "points": item["points"]}
                    for item in profile["bubbles"][channel]
                ]
                for channel in CHANNELS
            }
        },
        "notes": {"wet_geometry": "Derived exclusively from CAD intersect ROI intersect interest zone"},
    }
    write_json(analysis_path, analysis_payload)
    build_cad_masks(root / "assets" / "cad_pair_lines.npz", roi_payload, cad_masks_path)
    return profile, roi_path, analysis_path, cad_masks_path


def command_for_profile(profile_name: str, check: bool = False) -> list[str]:
    root = project_root()
    profile, roi_path, analysis_path, cad_masks_path = generate_compatibility_files(profile_name)
    command = [
        sys.executable,
        str(root / "fluid_phase_pipeline_v2.py"),
        "--video", str(root / "assets" / "reference.mp4"),
        "--project", str(roi_path),
        "--analysis-project", str(analysis_path),
        "--frame", str(profile["frame"]["index"]),
        "--refine-masks",
        "--cad-authoritative",
        "--cad-roi-masks", str(cad_masks_path),
        "--cad-outline-lines", str(root / "assets" / "cad_pair_lines.npz"),
        "--cad-vector-lines", str(root / "assets" / "cad_pair_vector_lines.json"),
        "--cad-placement-config", str(root / "assets" / "cad_placement.json"),
        "--bubble-smooth-radius", str(profile["settings"].get("bubble_smooth_radius", 3)),
        "--output-root", str(profile_path(profile_name).parent / "runs"),
    ]
    if profile["settings"].get("equalize_cad_lengths", True):
        command.append("--equalize-cad-lengths")
    if check:
        command.append("--check")
    return command


def main() -> int:
    args = parse_args()
    command = command_for_profile(args.profile, args.check)
    completed = subprocess.run(command, cwd=project_root())
    return int(completed.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
