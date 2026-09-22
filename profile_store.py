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


LEGACY_CHANNELS = ("CH1-1", "CH1-2", "CH2-1", "CH2-2")
PROFILE_SCHEMA = 2
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


def _raw_profile(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _legacy_virtual_name(base: str, channel: str) -> str:
    return f"{base}_{channel}"


def _find_legacy_virtual(name: str) -> tuple[Path, str] | None:
    for path in profiles_root().glob("*/profile.json"):
        payload = _raw_profile(path)
        if int(payload.get("schema_version", -1)) != 1:
            continue
        base = str(payload.get("name") or path.parent.name)
        for channel in LEGACY_CHANNELS:
            if name == _legacy_virtual_name(base, channel):
                return path, channel
    return None


def _migrate_legacy(payload: dict[str, Any], channel: str) -> dict[str, Any]:
    group = channel.split("-", 1)[0]
    migrated = {
        "schema_version": PROFILE_SCHEMA,
        "name": _legacy_virtual_name(str(payload.get("name", "profile")), channel),
        "description": f"Migrated v1 setup for {channel}",
        "frame": copy.deepcopy(payload.get("frame", {})),
        "source_video": copy.deepcopy(payload.get("source_video", {})),
        "geometry": {
            "interest_zone": copy.deepcopy(payload.get("interest_zones", {}).get(f"ZONE-{group}", [])),
            "analysis_roi": copy.deepcopy(payload.get("rois", {}).get(channel, [])),
            "calibration_roi": copy.deepcopy(payload.get("calibration_rois", {}).get(f"CAL-{group}", [])),
            "bubbles": copy.deepcopy(payload.get("bubbles", {}).get(channel, [])),
        },
        "cad": {"enabled": True, "legacy_channel": channel},
        "settings": copy.deepcopy(payload.get("settings", {})),
    }
    migrated["settings"]["flip_horizontal"] = channel.startswith("CH2")
    return migrated


def list_profiles() -> list[str]:
    if not profiles_root().exists():
        return []
    names: list[str] = []
    for path in profiles_root().glob("*/profile.json"):
        payload = _raw_profile(path)
        if int(payload.get("schema_version", -1)) == 1:
            base = str(payload.get("name") or path.parent.name)
            names.extend(_legacy_virtual_name(base, channel) for channel in LEGACY_CHANNELS)
        else:
            names.append(path.parent.name)
    return sorted(set(names), key=str.casefold)


def _point(value: Any, label: str, width: int, height: int) -> list[float]:
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        raise ValueError(f"Invalid point in {label}")
    x, y = float(value[0]), float(value[1])
    if not (0 <= x < width and 0 <= y < height):
        raise ValueError(f"Point outside the {width}x{height} frame in {label}: ({x}, {y})")
    return [round(x, 6), round(y, 6)]


def _polygon(value: Any, label: str, width: int, height: int, required: bool = True) -> list[list[float]]:
    points = [_point(point, label, width, height) for point in (value or [])]
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
    frame = result.setdefault("frame", {"index": 0, "width": 0, "height": 0})
    width, height = int(frame.get("width", 0)), int(frame.get("height", 0))
    if width < 1 or height < 1:
        raise ValueError("Profile frame dimensions must be positive")
    frame["width"], frame["height"] = width, height
    frame["index"] = int(frame.get("index", 0))
    if frame["index"] < 0:
        raise ValueError("Frame index cannot be negative")
    source = result.setdefault("source_video", {})
    source["path"] = str(source.get("path", DEFAULT_VIDEO)).replace("\\", "/")
    source.setdefault("name", Path(source["path"]).name)
    source.setdefault("fps", 30.0)
    source.setdefault("frame_count", 0)
    geometry = result.setdefault("geometry", {})
    geometry["interest_zone"] = _polygon(geometry.get("interest_zone", []), "Interest Zone", width, height, require_complete)
    geometry["analysis_roi"] = _polygon(geometry.get("analysis_roi", []), "Analysis ROI", width, height, require_complete)
    geometry["calibration_roi"] = _polygon(geometry.get("calibration_roi", []), "Calibration ROI", width, height, require_complete)
    clean_bubbles = []
    seen: set[str] = set()
    for index, item in enumerate(geometry.get("bubbles", []), start=1):
        item_id = str(item.get("id") or f"BUBBLE-{index:03d}")
        if item_id in seen:
            raise ValueError(f"Duplicate bubble id: {item_id}")
        seen.add(item_id)
        clean_bubbles.append({"id": item_id, "points": _polygon(item.get("points", []), item_id, width, height)})
    geometry["bubbles"] = clean_bubbles
    cad = result.setdefault("cad", {})
    cad["enabled"] = bool(cad.get("enabled", False))
    if cad["enabled"] and cad.get("legacy_channel") not in LEGACY_CHANNELS:
        raise ValueError("CAD profiles require a valid migrated legacy_channel")
    settings = result.setdefault("settings", {})
    settings.setdefault("bubble_smooth_radius", 3)
    settings.setdefault("flip_horizontal", False)
    return result


def load_profile(name: str, require_complete: bool = False) -> dict[str, Any]:
    path = profile_path(name)
    if path.exists():
        payload = _raw_profile(path)
        if int(payload.get("schema_version", -1)) == 1:
            raise ValueError(f"Select one of the profiles derived from {name}")
        return validate_profile(payload, require_complete)
    legacy = _find_legacy_virtual(name)
    if legacy is None:
        raise FileNotFoundError(f"Profile not found: {name}")
    legacy_path, channel = legacy
    return validate_profile(_migrate_legacy(_raw_profile(legacy_path), channel), require_complete)


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
    destination_dir = profile_path(name).parent / "source"
    destination_dir.mkdir(parents=True, exist_ok=True)
    destination = destination_dir / f"{safe_stem}_{digest.hexdigest()[:12]}{suffix}"
    if source != destination and not destination.exists():
        temporary = destination.with_suffix(destination.suffix + ".copying")
        try:
            shutil.copy2(source, temporary)
            os.replace(temporary, destination)
        except Exception:
            temporary.unlink(missing_ok=True)
            raise
    return destination, Path("source", destination.name).as_posix()


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
    source_video = resolve_profile_video(source_name, payload)
    payload["name"] = slugify(new_name)
    payload.pop("updated_at_utc", None)
    path = save_profile(payload, require_complete=False)
    if source_video.is_file() and source_video.parent.name == "source":
        destination, relative = copy_video_into_profile(path.parent.name, source_video)
        payload["source_video"]["path"] = relative
        payload["source_video"]["stored_name"] = destination.name
        path = save_profile(payload, require_complete=False)
    return path


def profile_completeness(payload: dict[str, Any]) -> tuple[bool, list[str]]:
    geometry = payload.get("geometry", {})
    missing = [label for key, label in (("interest_zone", "Interest Zone"), ("analysis_roi", "Analysis ROI"), ("calibration_roi", "Calibration ROI")) if len(geometry.get(key, [])) < 3]
    return not missing, missing
