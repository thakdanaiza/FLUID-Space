from __future__ import annotations

import argparse
import subprocess
import sys

from profile_store import load_profile, project_root, resolve_profile_video


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run one FLUID-Space v2 profile")
    parser.add_argument("--profile", default="current_baseline_CH1-1")
    parser.add_argument("--check", action="store_true")
    return parser.parse_args()


def command_for_profile(profile_name: str, check: bool = False) -> list[str]:
    profile = load_profile(profile_name, require_complete=True)
    video_path = resolve_profile_video(profile_name, profile)
    if not video_path.is_file():
        raise FileNotFoundError(f"Profile video not found: {video_path}")
    command = [
        sys.executable,
        str(project_root() / "single_profile_pipeline.py"),
        "--profile",
        profile_name,
    ]
    if check:
        command.append("--check")
    return command


def main() -> int:
    args = parse_args()
    completed = subprocess.run(command_for_profile(args.profile, args.check), cwd=project_root())
    return int(completed.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
