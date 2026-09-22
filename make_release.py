from __future__ import annotations

import hashlib
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent
VERSION = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
RELEASE_DIR = ROOT / "releases"

COMMON_FILES = {
    "CITATION.cff",
    "CHANGELOG.md",
    "LICENSE",
    "METHODS.md",
    "README.md",
    "REPRODUCIBILITY.md",
    "VERSION",
    "app.py",
    "cad_mask.py",
    "environment.yml",
    "fluid_io.py",
    "phase_analysis_core.py",
    "profile_store.py",
    "requirements.txt",
    "run_profile.py",
    "single_profile_pipeline.py",
    "DATA_PUBLICATION.md",
    "tools/prepare_research_dataset.py",
}

PLATFORMS = {
    "Windows": {
        "files": {"setup_env.bat", "start_ui.bat", "run_current_profile.bat"},
        "start_here": """FLUID-Space v{version} — Windows

1. Install 64-bit Python 3.12 from https://www.python.org/downloads/windows/
2. Double-click setup_env.bat and wait for Environment check passed.
3. Double-click start_ui.bat.

Use run_current_profile.bat to run the default baseline without opening the editor.
See README.md for the analysis method, citation, and complete instructions.
""",
    },
    "macOS": {
        "files": {"setup_env.sh", "start_ui.sh", "start_ui_mac.command", "run_current_profile.sh"},
        "start_here": """FLUID-Space v{version} — macOS

1. Install Python 3.12 from https://www.python.org/downloads/macos/
2. In Terminal, cd into this extracted folder.
3. Run: bash setup_env.sh
4. Run: bash start_ui.sh

After setup, start_ui_mac.command can be opened from Finder. If macOS blocks it,
right-click it, choose Open, and confirm.
See README.md for the analysis method, citation, and complete instructions.
""",
    },
}


def application_files(platform_files: set[str]) -> list[Path]:
    selected = [ROOT / name for name in sorted(COMMON_FILES | platform_files)]
    selected.extend(sorted(path for path in (ROOT / "assets").rglob("*") if path.is_file()))
    selected.append(ROOT / "profiles" / "current_baseline" / "profile.json")
    missing = [path for path in selected if not path.is_file()]
    if missing:
        raise FileNotFoundError("Release input is missing: " + ", ".join(str(path) for path in missing))
    return selected


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_archive(platform: str, config: dict[str, object]) -> Path:
    archive = RELEASE_DIR / f"FLUID-Space-v{VERSION}-{platform}.zip"
    prefix = Path(f"FLUID-Space-v{VERSION}-{platform}")
    files = application_files(set(config["files"]))
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
        bundle.writestr(str(prefix / "START_HERE.txt"), str(config["start_here"]).format(version=VERSION))
        for path in files:
            relative = path.relative_to(ROOT)
            info = zipfile.ZipInfo.from_file(path, str(prefix / relative))
            if path.suffix in {".sh", ".command"}:
                info.external_attr = (0o100755 & 0xFFFF) << 16
            with path.open("rb") as handle:
                bundle.writestr(info, handle.read(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    print(f"Created: {archive.name} ({len(files) + 1} files, {archive.stat().st_size / (1024 * 1024):.1f} MB)")
    return archive


def main() -> None:
    RELEASE_DIR.mkdir(exist_ok=True)
    archives = [build_archive(platform, config) for platform, config in PLATFORMS.items()]
    checksum_path = RELEASE_DIR / f"FLUID-Space-v{VERSION}-SHA256SUMS.txt"
    checksum_path.write_text(
        "".join(f"{sha256(path)}  {path.name}\n" for path in archives),
        encoding="utf-8",
    )
    print(f"Created: {checksum_path.name}")


if __name__ == "__main__":
    main()
