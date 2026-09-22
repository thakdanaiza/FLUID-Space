from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import cv2
import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from cad_mask import enclosed_regions
from fluid_io import read_video_frame
from phase_analysis_core import (
    LOW_S_THRESHOLDS,
    calibrate_marked_swatch,
    calculate_phase,
    channel_bounds,
    column_statistics,
    compose_channel_masks,
    mask_qc_bgr,
    polygon_mask,
    polygon_union_mask,
)
from profile_store import load_profile, profile_path, resolve_profile_video


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def next_run_directory(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    number = 1
    while (root / f"run_{number:03d}").exists():
        number += 1
    result = root / f"run_{number:03d}"
    result.mkdir()
    return result


def save_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def save_mask(path: Path, mask: np.ndarray) -> None:
    if not cv2.imwrite(str(path), mask.astype(np.uint8) * 255):
        raise RuntimeError(f"Cannot write {path}")


def cad_mask_for_profile(profile: dict[str, Any], shape: tuple[int, int], seed: np.ndarray) -> tuple[np.ndarray, np.ndarray | None]:
    cad = profile.get("cad", {})
    if not cad.get("enabled", False):
        return seed, None
    channel = str(cad.get("legacy_channel", ""))
    group = channel.split("-", 1)[0]
    lines_path = Path(__file__).resolve().parent / "assets" / "cad_pair_lines.npz"
    with np.load(lines_path, allow_pickle=False) as payload:
        line_mask = np.asarray(payload[f"pair_{group}"]).astype(bool)
    if line_mask.shape != shape:
        raise ValueError("Legacy CAD can only be used with its original frame dimensions")
    regions = enclosed_regions(line_mask)
    if not regions:
        raise ValueError(f"No enclosed CAD region found for {group}")
    scores = [int((region & seed).sum()) for region in regions]
    selected = regions[int(np.argmax(scores))]
    if max(scores) <= 0:
        raise ValueError("Analysis ROI does not overlap the selected CAD region")
    inner_stroke = line_mask & (cv2.dilate(selected.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))) > 0)
    return seed & (selected | inner_stroke), line_mask


def save_phase_image(path: Path, phase: np.ndarray, valid: np.ndarray) -> None:
    normalized = np.clip(phase - 1.0, 0.0, 1.0)
    rgb = np.rint(plt.get_cmap("turbo")(np.nan_to_num(normalized, nan=0.0))[:, :, :3] * 255).astype(np.uint8)
    rgb[~valid] = 0
    cv2.imwrite(str(path), cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR))


def save_profile_graph(path: Path, means: np.ndarray, counts: np.ndarray, cumulative: np.ndarray) -> None:
    x = np.arange(means.size)
    figure, (top, bottom) = plt.subplots(2, 1, figsize=(9, 5.8), sharex=True, gridspec_kw={"height_ratios": [3, 1]})
    top.plot(x, means, color="#2d6cdf", linewidth=1.3, label="Column mean")
    top.plot(x, cumulative, color="#d9485f", linewidth=1.8, label="Cumulative mean")
    top.set_ylim(1.0, 2.0)
    top.set_ylabel("Phase index")
    top.grid(alpha=0.22)
    top.legend()
    bottom.fill_between(x, counts, color="#5d8f70", alpha=0.8)
    bottom.set_ylabel("Pixels")
    bottom.set_xlabel("Flow direction (pixels)")
    bottom.grid(alpha=0.2)
    figure.tight_layout()
    figure.savefig(path, dpi=180)
    plt.close(figure)


def run(profile_name: str, check: bool = False) -> Path | None:
    profile = load_profile(profile_name, require_complete=True)
    video_path = resolve_profile_video(profile_name, profile)
    frame_index = int(profile["frame"]["index"])
    frame = read_video_frame(video_path, frame_index)
    shape = frame.bgr.shape[:2]
    expected = (int(profile["frame"]["height"]), int(profile["frame"]["width"]))
    if shape != expected:
        raise ValueError(f"Profile dimensions {expected[1]}x{expected[0]} do not match video {shape[1]}x{shape[0]}")

    geometry = profile["geometry"]
    zone = polygon_mask(shape, geometry["interest_zone"])
    roi = polygon_mask(shape, geometry["analysis_roi"])
    seed = zone & roi
    wet, cad_outline = cad_mask_for_profile(profile, shape, seed)
    calibration_mask = polygon_mask(shape, geometry["calibration_roi"])
    bubble_mask = polygon_union_mask(shape, [item["points"] for item in geometry["bubbles"]])
    empty = np.zeros(shape, dtype=bool)
    masks = compose_channel_masks("PROFILE", wet, wet, wet, calibration_mask, empty, bubble_mask, empty)
    calibration = calibrate_marked_swatch(frame.bgr, {"calibration_rois": {"CAL": geometry["calibration_roi"]}}, "CAL")
    phase = calculate_phase(frame.bgr, masks, calibration)
    left, top, right, bottom = channel_bounds(phase.valid_mask)
    phase_crop = phase.phase[top:bottom, left:right]
    valid_crop = phase.valid_mask[top:bottom, left:right]
    if bool(profile.get("settings", {}).get("flip_horizontal", False)):
        phase_crop, valid_crop = np.fliplr(phase_crop), np.fliplr(valid_crop)
    means, counts, cumulative = column_statistics(phase_crop, valid_crop)
    if check:
        print(profile_name, masks.summary(), phase.summary())
        return None

    run_dir = next_run_directory(profile_path(profile_name).parent / "runs")
    array_dir, qc_dir, graph_dir = run_dir / "arrays", run_dir / "qc", run_dir / "graphs"
    for directory in (array_dir, qc_dir, graph_dir):
        directory.mkdir()
    np.save(array_dir / "phase_raw.npy", phase.phase)
    np.save(array_dir / "valid_mask.npy", phase.valid_mask)
    np.save(array_dir / "phase_crop_flow_oriented.npy", phase_crop)
    save_mask(array_dir / "valid_mask.png", phase.valid_mask)
    save_phase_image(qc_dir / "phase.png", phase.phase, phase.valid_mask)
    for view in ("wet", "exclusions", "final"):
        cv2.imwrite(str(qc_dir / f"mask_{view}.png"), mask_qc_bgr(frame.bgr, masks, view))
    if cad_outline is not None:
        preview = frame.bgr.copy()
        preview[cad_outline] = (255, 255, 255)
        cv2.imwrite(str(qc_dir / "cad_outline_overlay.png"), preview)
    save_profile_graph(graph_dir / "phase_profile.png", means, counts, cumulative)
    save_phase_image(graph_dir / "phase_result.png", phase_crop, valid_crop)

    phase_summary = phase.summary()
    summary = {
        "pipeline": "single_profile_pipeline_v2",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "profile": profile_name,
        "video": {"path": str(video_path), "sha256": file_sha256(video_path)},
        "frame": frame_index,
        "mode": "legacy_cad" if profile.get("cad", {}).get("enabled") else "roi_only",
        "flow_flipped": bool(profile.get("settings", {}).get("flip_horizontal", False)),
        "calibration": calibration.summary(),
        "mask": masks.summary(),
        "phase": phase_summary,
        "flow_crop_original_bbox": [left, top, right, bottom],
        "low_s_thresholds": list(LOW_S_THRESHOLDS),
    }
    save_json(run_dir / "summary.json", summary)
    with (run_dir / "summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=("profile", "valid_pixels", "mean_index", "std_index", "final_cumulative_index"))
        writer.writeheader()
        writer.writerow({"profile": profile_name, **{key: phase_summary[key] for key in ("valid_pixels", "mean_index", "std_index", "final_cumulative_index")}})
    print(f"V2 result: {run_dir}")
    return run_dir


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run one FLUID-Space v2 profile")
    parser.add_argument("--profile", default="current_baseline_CH1-1")
    parser.add_argument("--check", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        run(args.profile, args.check)
        return 0
    except Exception as exc:
        print(f"V2 pipeline stopped ({type(exc).__name__}): {exc}")
        traceback.print_exc(file=sys.stdout)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
