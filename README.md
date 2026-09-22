# FLUID-Space v2

FLUID-Space creates calibrated phase maps from experiment videos. In v2, one profile is one complete analysis setup. There is no channel selector: choose a profile, choose its video and frame, edit its geometry, then run it.

Profiles can use the supplied legacy CAD boundary or work in ROI-only mode for videos that do not use the CH1/CH2 layout. ROI-only profiles may use any positive video resolution.

## Install

FLUID-Space supports Windows 10/11 and current Intel or Apple Silicon Macs with Python 3.12. Conda is optional.

On Windows, extract the release and run `setup_env.bat`, then open `start_ui.bat`.

On macOS, run:

```bash
bash setup_env.sh
bash start_ui.sh
```

## Profile model

Each v2 profile stores one:

- Source video and analysis frame
- Interest Zone
- Analysis ROI
- Calibration ROI
- Set of bubble exclusions
- Flow direction
- Optional legacy CAD binding
- Independent result history

The v1 `current_baseline` is exposed automatically as four profiles:

- `current_baseline_CH1-1`
- `current_baseline_CH1-2`
- `current_baseline_CH2-1`
- `current_baseline_CH2-2`

This migration is non-destructive. The v1 source profile remains unchanged; saving one of the derived profiles creates its own schema-v2 profile.

## Use FLUID-Space

1. Select a profile at the top of the window. To make an independent setup, click **Duplicate as…**.
2. Click **Select video…** and choose the source clip.
3. Enter the analysis frame and click **Load**.
4. For a non-channel clip, turn off **Use legacy CAD boundary**. If the new video has a different resolution, confirm that the old geometry should be cleared.
5. Draw the **Interest Zone**, **Analysis ROI**, and **Calibration ROI**. Add any number of **Bubble** exclusions.
6. Enable **Reverse result direction** when flow should be reported from right to left.
7. Click **Save**, then **Run result**.

Drawing controls:

- Left click: add a point
- Right click or Enter: close the polygon
- Mouse wheel: zoom
- Middle-button drag: pan
- Esc: cancel the current polygon
- Ctrl+Z: remove the latest unfinished point
- Ctrl+S: save

The ROI-only analysis area is:

```text
Analysis ROI ∩ Interest Zone − Calibration ROI − Bubble exclusions
```

When legacy CAD is enabled, the CAD interior is also intersected with that area.

## Results

Each run is saved under:

```text
profiles/<profile-name>/runs/run_xxx/
```

The main result is `graphs/phase_result.png`. The run also contains the phase profile graph, NumPy arrays, masks, QC images, `summary.json`, and `summary.csv`.

## Command line and checks

Run a profile:

```bash
python run_profile.py --profile current_baseline_CH1-1
```

Validate it without creating a run folder:

```bash
python run_profile.py --profile current_baseline_CH1-1 --check
```

## Notes for existing v1 users

- Channel selection has been removed from the UI and runtime.
- A profile can no longer contain four setups; duplicate or select one profile per setup.
- Legacy CAD metadata is retained only for migrated CAD profiles.
- Selecting a different-resolution video clears incompatible geometry after confirmation and switches the profile to ROI-only mode.
- The original four-channel pipeline remains in the source tree for reproducibility of v1 analyses, but v2 profiles run through `single_profile_pipeline.py`.

## Citing FLUID-Space

Cite the exact release used. Example:

> Image analysis was performed using FLUID-Space v2.0.0 (Author et al., 2026), using one independently stored analysis setup per profile.

Replace author, institution, repository, and DOI placeholders with the release's archived metadata.
