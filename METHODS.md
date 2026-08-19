# FLUID-Space Research Methods Reference

This file describes the analysis implemented in FLUID-Space v1.0.0 and provides manuscript-ready language for laboratory studies. Confirm the software version, selected frame, profile, and study-specific acquisition details before reusing the text.

## Method summary

FLUID-Space analyzes one selected frame from a 1090 x 340 pixel experiment video. Four channels are processed: CH1-1, CH1-2, CH2-1, and CH2-2. The physical fluid geometry is defined by the registered CAD layout. Operator-drawn Interest Zones and channel ROIs can remove CAD pixels but cannot add pixels outside the CAD interior.

For channel `c`, the initial analysis mask is:

```text
M_geometry,c = M_CAD,c ∩ M_ROI,c ∩ M_interest-zone,g
```

where `g` is CH1 or CH2. Enclosed internal CAD holes remain outside the mask. Legacy manually placed island exclusions are disabled in CAD-authoritative mode.

Calibration-swatch areas and manually marked bubbles are removed. The final mask is:

```text
M_final,c = M_geometry,c − (M_calibration ∪ M_bubble,c ∪ M_artifact,c)
```

The current profile workflow does not expose a separate artifact-drawing tool; its routine exclusion input is the Bubble tool.

## Bubble handling

Each operator-drawn bubble polygon is a hard exclusion. FLUID-Space may refine the bubble boundary using OpenCV GrabCut within a narrow search region around the polygon. The current pipeline uses five GrabCut iterations, a 3-pixel boundary width, and conservative acceptance gates:

- Boundary change must not exceed 22% of the manually drawn area.
- Refined area must remain between 0.70 and 1.30 times the drawn area.
- Added pixels must not reach the search-region limit.

Rejected refinements fall back to the manual polygon. Accepted masks are rounded by elliptical morphological opening and closing with the profile's smoothing radius (3 pixels in the current baseline). The manual polygon is then unioned back into the refined mask, ensuring that no manually marked pixel is restored to the phase result.

## Color calibration

CH1 and CH2 use separate calibration regions. Each marked calibration region is divided into four interior patches. The mean RGB color of each patch is converted to HSV. Patches with saturation below 0.2 are omitted from calibration. Each remaining hue is matched to the nearest circular reference hue among 0, 1/3, and 2/3, and the mean circular hue difference is used as the group-specific hue shift.

## Phase-index calculation

The selected video frame is converted from RGB to HSV. Hue is normalized to the interval [0, 1) and corrected by the group-specific calibration shift. Circular hue distance is calculated to the fixed reference centers:

```text
h_oil   = 0.110
h_water = 0.465
```

For every valid pixel, the phase index is:

```text
d_oil   = circular_distance(h, h_oil)
d_water = circular_distance(h, h_water)
P       = 1 + d_water / (d_oil + d_water + epsilon)
```

The index ranges from approximately 1 to 2, where 1 represents the water reference and 2 represents the oil reference. Pixels outside the final mask are stored as missing values rather than assigned a phase value.

Low-saturation pixels are included in the primary result. FLUID-Space reports sensitivity checks after excluding pixels below saturation thresholds of 0.05, 0.10, and 0.15. A sensitivity result is flagged when its final cumulative index differs from the primary result by more than 0.02.

## Spatial summaries

For each image column, FLUID-Space reports the mean phase index and valid-pixel count. The cumulative index at column `x` is the valid-pixel-weighted mean of all valid pixels from the flow origin through that column. CH2 channels are flipped horizontally so all publication profiles follow a common flow direction.

When CAD-length equalization is enabled, the longer CH group is trimmed from the figure-right side to match the shorter Interest Zone width. The current baseline profile enables this option.

## Quality control and provenance

Each run is stored in `profiles/<profile-name>/runs/run_xxx/`. Retain the following files with the study record:

- `summary.json` and `summary.csv`
- `profile.json`
- The selected source video or its archived copy
- `arrays/valid_mask_*.npy` and `arrays/phase_raw_*.npy`
- `qc/mask_final_*.png` and `qc/phase_*.png`
- `graphs/phase_publication_aligned_left.png`

`summary.json` records the selected frame, input paths and SHA-256 hashes, mask statistics, calibration values, phase summaries, low-saturation sensitivity results, and bubble-refinement acceptance or fallback information.

Before accepting a run, visually inspect the final mask for all four channels and confirm that CAD holes, calibration regions, and marked bubbles contain no phase color. Also review the selected frame and verify that the profile belongs to the correct experiment.

## Manuscript-ready template

Replace every item in square brackets before use:

> A representative frame (frame [FRAME_NUMBER], time [TIME_S] s) was extracted from each experiment video ([WIDTH] x [HEIGHT] pixels, [FRAME_RATE] frames s-1) and analyzed using FLUID-Space v[VERSION] ([REPOSITORY OR DOI]). Four channel regions (CH1-1, CH1-2, CH2-1, and CH2-2) were evaluated. The analysis geometry was defined from a registered CAD layout and intersected with experiment-specific channel regions of interest and CH-group Interest Zones. Calibration-swatch regions and manually annotated gas bubbles were excluded. Bubble boundaries were conservatively refined within a [BOUNDARY_WIDTH]-pixel neighborhood using GrabCut and elliptical morphological smoothing; the original annotation remained a hard exclusion. Pixel colors were converted to HSV and corrected using group-specific calibration swatches. Corrected hue was mapped to a phase index using circular distances to fixed water (h = 0.465) and oil (h = 0.110) reference centers, yielding an index from 1 (water) to 2 (oil). Channel-wise phase maps, longitudinal means, valid-pixel counts, and cumulative valid-pixel-weighted indices were exported. Low-saturation sensitivity analyses were evaluated at S = 0.05, 0.10, and 0.15. Masks and quality-control images were visually reviewed before statistical analysis.

## Minimum information to report

- FLUID-Space version and repository, DOI, or archived release
- Operating system and Python version when required by the journal
- Camera and acquisition settings
- Video resolution, frame rate, and compression format
- Rule used to select the analyzed frame or frames
- Profile name and whether geometry was reused across experiments
- CAD registration procedure and any experiment-specific Interest Zone/ROI changes
- Bubble-marking procedure and number of operators
- Bubble boundary width, maximum-change gate, and smoothing radius
- Whether CAD-length equalization was enabled
- Primary endpoint: pixel-level map, channel mean, terminal cumulative index, or another derived quantity
- Number of biological and technical replicates
- Blinding, randomization, exclusions, and statistical methods
- Retained provenance files and data/code availability statement

## Important interpretation limits

The phase index is a calibrated hue-distance index, not automatically a volumetric phase fraction. A study should not describe it as oil fraction, water saturation, concentration, or holdup unless that relationship has been independently validated for the optical setup, dyes, illumination, camera, channel material, and fluid system used in that study.

FLUID-Space v1.0.0 analyzes a selected frame per run. A time-series study must define its frame-sampling strategy and repeat the analysis consistently; the current UI does not automatically aggregate an entire video into a temporal endpoint.
