from __future__ import annotations

import copy
import hashlib
import json
import os
import re
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


CHANNELS = ("CH1-1", "CH1-2", "CH2-1", "CH2-2")
ZONES = ("ZONE-CH1", "ZONE-CH2")
PROFILE_SCHEMA = 1
DEFAULT_VIDEO = "../../assets/reference.mp4"


def project_root() -> Path:
    return Path(__file__).resolve().parent


def profiles_root() -> Path:
    return project_root() / "profiles"


def slugify(name: str) -> str:
    value = re.sub(r"[^A-Za-z0-9_-]+", "_", name.strip()).strip("_")
    if not value:
        raise ValueError("Profile name must contain at least one letter or number")
    return value


def profile_path(name: str) -> Path:
    return profiles_root() / slugify(name) / "profile.json"


def resolve_profile_video(name: str, payload: dict[str, Any] | None = None) -> Path:
    profile = payload if payload is not None else load_profile(name, require_complete=False)
    relative = Path(str(profile.get("source_video", {}).get("path", DEFAULT_VIDEO)))
    if relative.is_absolute():
        raise ValueError("Profile video path must be relative to the profile folder")
    resolved = (profile_path(name).parent / relative).resolve()
    try:
        resolved.relative_to(project_root().resolve())
    except ValueError as exc:
        raise ValueError("Profile video must be stored inside the FLUID-Space project") from exc
    return resolved


def copy_video_into_profile(name: str, source: Path) -> tuple[Path, str]:
    source = source.resolve()
    if not source.is_file():
        raise FileNotFoundError(f"Video not found: {source}")
    digest = hashlib.sha256()
    with source.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    safe_stem = re.sub(r"[^A-Za-z0-9_-]+", "_", source.stem).strip("_") or "video"
    suffix = source.suffix.lower() or ".mp4"
    filename = f"{safe_stem}_{digest.hexdigest()[:12]}{suffix}"
    destination_dir = profile_path(name).parent / "source"
    destination_dir.mkdir(parents=True, exist_ok=True)
    if source.parent.resolve() == destination_dir.resolve():
        return source, Path("source", source.name).as_posix()
    destination = destination_dir / filename
    if not destination.exists():
        temporary = destination.with_suffix(destination.suffix + ".copying")
        try:
            shutil.copy2(source, temporary)
            os.replace(temporary, destination)
        except Exception:
            temporary.unlink(missing_ok=True)
            raise
    return destination, Path("source", filename).as_posix()


def list_profiles() -> list[str]:
    root = profiles_root()
    if not root.exists():
        return []
    names = [path.parent.name for path in root.glob("*/profile.json")]
    return sorted(names, key=str.casefold)


def _point(value: Any, label: str) -> list[float]:
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        raise ValueError(f"Invalid point in {label}")
    x, y = float(value[0]), float(value[1])
    if not (0 <= x < 1090 and 0 <= y < 340):
        raise ValueError(f"Point outside the 1090x340 frame in {label}: ({x}, {y})")
    return [round(x, 6), round(y, 6)]


def _polygon(value: Any, label: str, required: bool = True) -> list[list[float]]:
    points = [_point(point, label) for point in (value or [])]
    if required and len(points) < 3:
        raise ValueError(f"{label} needs at least 3 points")
    if points and len(points) < 3:
        raise ValueError(f"{label} has fewer than 3 points")
    return points


def validate_profile(payload: dict[str, Any], require_complete: bool = True) -> dict[str, Any]:
    if int(payload.get("schema_version", -1)) != PROFILE_SCHEMA:
        raise ValueError(f"Unsupported profile schema: {payload.get('schema_version')}")
    result = copy.deepcopy(payload)
    result["name"] = slugify(str(result.get("name", "")))
    result.setdefault("frame", {"index": 120, "width": 1090, "height": 340})
    if (int(result["frame"].get("width", 0)), int(result["frame"].get("height", 0))) != (1090, 340):
        raise ValueError("This baseline requires a 1090x340 source frame")
    frame_index = int(result["frame"].get("index", 120))
    if frame_index < 0:
        raise ValueError("Frame index cannot be negative")
    result["frame"]["index"] = frame_index
    source_video = result.setdefault("source_video", {})
    source_video["path"] = str(source_video.get("path", DEFAULT_VIDEO)).replace("\\", "/")
    source_video.setdefault("name", Path(source_video["path"]).name)
    source_video.setdefault("fps", 30.0)
    source_video.setdefault("frame_count", 0)
    zones = result.setdefault("interest_zones", {})
    rois = result.setdefault("rois", {})
    bubbles = result.setdefault("bubbles", {})
    for name in ZONES:
        zones[name] = _polygon(zones.get(name, []), name, require_complete)
    for name in CHANNELS:
        rois[name] = _polygon(rois.get(name, []), f"ROI {name}", require_complete)
        clean_items = []
        seen = set()
        for index, item in enumerate(bubbles.get(name, []), start=1):
            item_id = str(item.get("id") or f"{name}-BUBBLE-{index:03d}")
            if item_id in seen:
                raise ValueError(f"Duplicate bubble id: {item_id}")
            seen.add(item_id)
            clean_items.append({"id": item_id, "points": _polygon(item.get("points", []), item_id)})
        bubbles[name] = clean_items
    calibrations = result.setdefault("calibration_rois", {})
    for name in ("CAL-CH1", "CAL-CH2"):
        calibrations[name] = _polygon(calibrations.get(name, []), name)
    result.setdefault("settings", {})
    result["settings"].setdefault("bubble_smooth_radius", 3)
    result["settings"].setdefault("equalize_cad_lengths", True)
    return result


def load_profile(name: str, require_complete: bool = False) -> dict[str, Any]:
    path = profile_path(name)
    if not path.exists():
        raise FileNotFoundError(f"Profile not found: {name}")
    return validate_profile(json.loads(path.read_text(encoding="utf-8")), require_complete)


def save_profile(payload: dict[str, Any], require_complete: bool = False) -> Path:
    clean = validate_profile(payload, require_complete)
    clean["updated_at_utc"] = datetime.now(timezone.utc).isoformat()
    path = profile_path(clean["name"])
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=".profile_", suffix=".json", dir=path.parent, text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(clean, handle, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    except Exception:
        Path(temp_name).unlink(missing_ok=True)
        raise
    return path


def duplicate_profile(source_name: str, new_name: str) -> Path:
    payload = load_profile(source_name, require_complete=False)
    destination_name = slugify(new_name)
    source_video = resolve_profile_video(source_name, payload)
    source_dir = (profile_path(source_name).parent / "source").resolve()
    payload["name"] = destination_name
    payload.pop("updated_at_utc", None)
    if source_video.is_file() and source_video.is_relative_to(source_dir):
        destination_dir = profile_path(destination_name).parent / "source"
        destination_dir.mkdir(parents=True, exist_ok=True)
        destination = destination_dir / source_video.name
        if not destination.exists():
            shutil.copy2(source_video, destination)
        payload["source_video"]["path"] = Path("source", destination.name).as_posix()
    return save_profile(payload, require_complete=False)


def profile_completeness(payload: dict[str, Any]) -> tuple[bool, list[str]]:
    missing = []
    for name in ZONES:
        if len(payload.get("interest_zones", {}).get(name, [])) < 3:
            missing.append(name)
    for name in CHANNELS:
        if len(payload.get("rois", {}).get(name, [])) < 3:
            missing.append(f"ROI {name}")
    return not missing, missing
