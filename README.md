# FLUID-Space v2.0.1

FLUID-Space is a profile-based application for generating calibrated phase-index maps from experiment videos. One profile contains one complete analysis setup; the UI has no separate channel selector. Profiles may use the supplied legacy CAD boundary or an ROI-only workflow for videos outside the original CH1/CH2 layout.

## Authors and citation

- Thakdanai Sirisombat — Integration of Space and Human Advancement (ISHA), Chulabhorn Royal Academy; [ORCID 0000-0003-4360-3525](https://orcid.org/0000-0003-4360-3525); contact: <fifatein@gmail.com>
- Saran Seehanam — Integration of Space and Human Advancement (ISHA), Chulabhorn Royal Academy

Use GitHub's **Cite this repository** function, which reads [`CITATION.cff`](CITATION.cff), or cite the DOI shown on the latest archived release.

Suggested citation before a DOI is assigned:

> Sirisombat, T., & Seehanam, S. (2026). *FLUID-Space* (Version 2.0.1) [Computer software]. Integration of Space and Human Advancement (ISHA), Chulabhorn Royal Academy. https://github.com/thakdanaiza/FLUID-Space/releases/tag/v2.0.1

## License

FLUID-Space is released under the [MIT License](LICENSE). Copyright © 2026 Thakdanai Sirisombat, Saran Seehanam, and Integration of Space and Human Advancement (ISHA).

## Install

FLUID-Space supports Windows 10/11 and current Intel or Apple Silicon Macs with Python 3.12. Conda is optional.

Download the matching asset from the GitHub Release page:

- `FLUID-Space-v2.0.1-Windows.zip`
- `FLUID-Space-v2.0.1-macOS.zip`

Each package contains only the launchers for its operating system and a `START_HERE.txt`. GitHub's automatically generated source archives remain available for source inspection and reproducibility.

Windows:

1. Extract the release ZIP.
2. Run `setup_env.bat`.
3. Open `start_ui.bat`.

macOS:

```bash
bash setup_env.sh
bash start_ui.sh
```

For the exact environment used to test the research release:

```bash
conda env create -f environment.yml
conda activate fluid-space
python app.py --profile current_baseline_CH1-1
```

## Profile model and migration

Each v2 profile stores one source video, analysis frame, Interest Zone, Analysis ROI, Calibration ROI, bubble list, flow direction, optional legacy CAD binding, and independent result history.

The v1 `current_baseline` is exposed non-destructively as four profiles:

- `current_baseline_CH1-1`
- `current_baseline_CH1-2`
- `current_baseline_CH2-1`
- `current_baseline_CH2-2`

Saving a derived profile creates a schema-v2 profile without changing the v1 source JSON. User-created profile JSON, copied source videos, generated compatibility files, and run outputs are excluded from Git and source-release archives.

## Analysis method

### Geometry and masks

In ROI-only mode, the initial wet geometry is:

```text
M_wet = M_interest-zone ∩ M_analysis-ROI
```

In legacy-CAD mode:

```text
M_wet = M_CAD-interior ∩ M_interest-zone ∩ M_analysis-ROI
```

The final valid mask is:

```text
M_final = M_wet − (M_calibration ∪ M_bubbles)
```

Bubble polygons are hard exclusions in the active v2 single-profile pipeline. The pipeline does not restore excluded pixels.

### Calibration ROI

The Calibration ROI must contain a 2×2 color swatch and have a bounding box of at least 12×12 pixels. Four interior patches are sampled at fixed fractional positions. For each patch, mean RGB is converted to HSV; patches with saturation below `0.2` are ignored. Each retained hue is matched by circular distance to the nearest reference hue among `0`, `1/3`, and `2/3`. The mean circular measured-minus-reference difference is the hue correction shift. At least one saturated patch is required.

### Phase-index equation

For normalized measured hue `h0`:

```text
h       = (h0 − hue_shift) mod 1
d_oil   = circular_distance(h, 0.110)
d_water = circular_distance(h, 0.465)
P       = 1 + d_water / (d_oil + d_water + ε)
```

`P` is approximately 1 at the water reference and 2 at the oil reference. It is a calibrated hue-distance index, not automatically a volume fraction, concentration, saturation, or holdup. Such interpretations require independent validation for the optical setup, dyes, illumination, camera, channel material, and fluid system.

Low-saturation pixels remain in the primary result. Counts below `S = 0.05`, `0.10`, and `0.15` are recorded for quality control.

## Use FLUID-Space

1. Select or duplicate a profile.
2. Choose the source video and analysis frame.
3. For a non-channel clip, turn off **Use legacy CAD boundary**.
4. Draw the **Interest Zone**, **Analysis ROI**, and **Calibration ROI**; add bubble exclusions as needed.
5. Enable **Reverse result direction** when flow should be reported from right to left.
6. Save the profile and click **Run result**.

If a selected video has different dimensions, FLUID-Space requests confirmation before clearing incompatible geometry and switching to ROI-only mode.

Drawing controls:

- Left click: add a point
- Right click or Enter: close the polygon
- Mouse wheel: zoom
- Middle-button drag: pan
- Esc: cancel the current polygon
- Ctrl+Z: remove the latest unfinished point
- Ctrl+S: save

## Outputs

Runs are stored under `profiles/<profile-name>/runs/run_xxx/` and contain:

- `graphs/phase_result.png` — flow-oriented phase map
- `graphs/phase_profile.png` — column mean, cumulative mean, and valid-pixel count
- `arrays/phase_raw.npy` — phase index in original image coordinates; invalid pixels are `NaN`
- `arrays/valid_mask.npy` and `valid_mask.png`
- `arrays/phase_crop_flow_oriented.npy`
- `qc/phase.png`, final/wet/exclusion masks, and optional CAD overlay
- `summary.json` — full run provenance, calibration, mask, and phase summary
- `summary.csv` — compact profile-level result

## Command-line checks

```bash
python -m unittest discover -s tests -v
python run_profile.py --profile current_baseline_CH1-1 --check
python run_profile.py --profile current_baseline_CH1-1
```

See [METHODS.md](METHODS.md) for manuscript-ready method text and [REPRODUCIBILITY.md](REPRODUCIBILITY.md) for the tested environment and provenance checklist.
