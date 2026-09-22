# Changelog

All notable changes to FLUID-Space are documented in this file.

## 2.0.0 - 2026-09-22

Profile-first release for legacy channel experiments and generic videos.

### Changed

- Removed channel selection: one profile now contains exactly one analysis setup.
- Added non-destructive migration of the v1 baseline into four selectable profiles.
- Added one Interest Zone, Analysis ROI, Calibration ROI, and bubble list per profile.
- Added ROI-only processing for clips outside the legacy CH1/CH2 CAD layout.
- Removed the fixed 1090×340 restriction for ROI-only profiles.
- Added per-profile flow direction and optional legacy CAD binding.
- Added profile-scoped arrays, QC images, graphs, CSV, and JSON summaries.

The v1 baseline JSON stays unchanged, and the original four-channel pipeline remains in the source tree for reproducibility.

## 1.0.0 - 2026-08-19

First lab-ready release.

### Included

- CAD-authoritative geometry for CH1-1, CH1-2, CH2-1, and CH2-2.
- Profile-based Interest Zones, channel ROIs, and hard bubble exclusions.
- Source-video and analysis-frame binding for each profile.
- Conservative bubble-boundary refinement that never restores manually excluded pixels.
- Group-specific hue calibration and phase-index mapping from 1 (water) to 2 (oil).
- Channel QC, masks, arrays, summaries, publication figures, and provenance hashes.
- English desktop UI and profile duplication workflow.
- Windows and macOS setup/launch scripts without a Conda requirement.
- End-user README, Word user guide, and research Methods reference.
