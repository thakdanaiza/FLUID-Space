from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from profile_store import load_profile, resolve_profile_video, slugify  # noqa: E402


LICENSES = ("CC-BY-4.0", "CC0-1.0", "All-Rights-Reserved")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def dataset_slug(title: str) -> str:
    value = re.sub(r"[^A-Za-z0-9_-]+", "-", title.strip()).strip("-").lower()
    if not value:
        raise ValueError("Dataset title must contain at least one letter or number")
    return value


def portable_profile(name: str) -> tuple[dict[str, Any], Path, bytes]:
    profile = load_profile(name, require_complete=True)
    video_path = resolve_profile_video(name, profile)
    if not video_path.is_file():
        raise FileNotFoundError(f"Profile video not found: {video_path}")
    clean = copy.deepcopy(profile)
    clean["source_video"]["path"] = f"source/{video_path.name}"
    clean["source_video"]["stored_name"] = video_path.name
    clean.pop("updated_at_utc", None)
    encoded = (json.dumps(clean, indent=2, allow_nan=False) + "\n").encode("utf-8")
    return clean, video_path, encoded


def dataset_readme(title: str, data_license: str, profile_names: list[str]) -> str:
    profiles = "\n".join(f"- `{name}`" for name in profile_names)
    return f"""# {title}

This dataset contains experiment videos and their FLUID-Space v2.0.1 analysis profiles.

## Profiles

{profiles}

Each `profiles/<name>/profile.json` is paired with its video under the same profile's `source/` directory. To use the dataset, copy the `profiles` directory into a FLUID-Space v2.0.1 installation, select the profile in the UI, and run the profile check before analysis.

## Software

FLUID-Space v2.0.1: https://doi.org/10.5281/zenodo.22888466

## License

Dataset license: {data_license}

The FLUID-Space software is licensed separately under the MIT License.

## Integrity and provenance

`manifest.json` records the SHA-256, size, frame metadata, geometry mode, and analysis frame for every included profile and video. Verify the accompanying ZIP checksum after download. Study-specific acquisition conditions, sample definitions, frame-selection rules, and ethical or institutional approvals should be added to the Zenodo record before publication.
"""


def build_dataset(title: str, data_license: str, profile_names: list[str], output_dir: Path) -> tuple[Path, Path]:
    if len(set(profile_names)) != len(profile_names):
        raise ValueError("Each --profile value must be unique")
    output_dir.mkdir(parents=True, exist_ok=True)
    slug = dataset_slug(title)
    archive_path = output_dir / f"{slug}.zip"
    prefix = Path(slug)
    manifest: dict[str, Any] = {
        "schema_version": 1,
        "title": title,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "data_license": data_license,
        "software": {
            "name": "FLUID-Space",
            "version": "2.0.1",
            "repository": "https://github.com/thakdanaiza/FLUID-Space",
            "release": "https://github.com/thakdanaiza/FLUID-Space/releases/tag/v2.0.1",
            "doi": "10.5281/zenodo.22888466",
        },
        "profiles": [],
    }
    prepared: list[tuple[str, dict[str, Any], Path, bytes]] = []
    for requested_name in profile_names:
        name = slugify(requested_name)
        profile, video_path, profile_bytes = portable_profile(name)
        profile_relative = Path("profiles", name, "profile.json")
        video_relative = Path("profiles", name, "source", video_path.name)
        manifest["profiles"].append(
            {
                "name": name,
                "profile_path": profile_relative.as_posix(),
                "profile_sha256": sha256_bytes(profile_bytes),
                "video_path": video_relative.as_posix(),
                "video_sha256": sha256_file(video_path),
                "video_size_bytes": video_path.stat().st_size,
                "analysis_frame": int(profile["frame"]["index"]),
                "frame_width": int(profile["frame"]["width"]),
                "frame_height": int(profile["frame"]["height"]),
                "fps": float(profile["source_video"].get("fps", 0.0)),
                "frame_count": int(profile["source_video"].get("frame_count", 0)),
                "geometry_mode": "legacy_cad" if profile.get("cad", {}).get("enabled") else "roi_only",
                "flow_flipped": bool(profile.get("settings", {}).get("flip_horizontal", False)),
            }
        )
        prepared.append((name, profile, video_path, profile_bytes))

    manifest_bytes = (json.dumps(manifest, indent=2, allow_nan=False) + "\n").encode("utf-8")
    readme_bytes = dataset_readme(title, data_license, [item[0] for item in prepared]).encode("utf-8")
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
        bundle.writestr(str(prefix / "README.md"), readme_bytes)
        bundle.writestr(str(prefix / "manifest.json"), manifest_bytes)
        for name, _profile, video_path, profile_bytes in prepared:
            bundle.writestr(str(prefix / "profiles" / name / "profile.json"), profile_bytes)
            video_arcname = str(prefix / "profiles" / name / "source" / video_path.name)
            bundle.write(video_path, video_arcname, compress_type=zipfile.ZIP_STORED)

    checksum_path = output_dir / f"{archive_path.stem}-SHA256.txt"
    checksum_path.write_text(f"{sha256_file(archive_path)}  {archive_path.name}\n", encoding="utf-8")
    return archive_path, checksum_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a portable FLUID-Space research dataset for Zenodo")
    parser.add_argument("--title", required=True, help="Public dataset title")
    parser.add_argument("--data-license", required=True, choices=LICENSES)
    parser.add_argument("--profile", action="append", required=True, help="Saved profile name; repeat for multiple profiles")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "releases")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        archive, checksum = build_dataset(args.title, args.data_license, args.profile, args.output_dir)
    except Exception as exc:
        print(f"Dataset preparation failed ({type(exc).__name__}): {exc}", file=sys.stderr)
        return 1
    print(f"Created: {archive}")
    print(f"Created: {checksum}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
