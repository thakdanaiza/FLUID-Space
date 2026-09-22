# FLUID-Space v2.0.1 Research Methods Reference

This document describes the active single-profile pipeline implemented in FLUID-Space v2.0.1. Replace bracketed placeholders with study-specific acquisition and validation information before using the manuscript text.

## Analysis unit and profile binding

Each run analyzes one selected video frame through one saved profile. The profile binds the source video, frame index, image dimensions, Interest Zone, Analysis ROI, Calibration ROI, bubble polygons, flow orientation, and optional legacy CAD metadata. The source-video SHA-256 and run parameters are recorded in `summary.json`.

## Geometry and exclusion masks

For image coordinates `(x, y)`, ROI-only profiles define initial wet geometry as:

```text
M_wet(x,y) = M_interest-zone(x,y) ∩ M_analysis-ROI(x,y)
```

For profiles using the supplied legacy CAD layout:

```text
M_wet(x,y) = M_CAD-interior(x,y)
             ∩ M_interest-zone(x,y)
             ∩ M_analysis-ROI(x,y)
```

CAD interiors are obtained from enclosed regions of the registered line mask; the region overlapping the profile ROI is selected. The final valid mask is:

```text
M_final(x,y) = M_wet(x,y)
               − [M_calibration(x,y) ∪ M_bubbles(x,y)]
```

Calibration and bubble masks affect only pixels overlapping `M_wet`. Bubble polygons are hard exclusions in the v2.0.1 single-profile pipeline; automatic bubble-boundary refinement is not applied by this pipeline.

## Color calibration

The operator draws a polygon around a 2×2 calibration swatch. Its axis-aligned bounding box must be at least 12×12 pixels. Four interior sampling regions are defined as fractions of that bounding box:

```text
top-left:     x = 0.05–0.45, y = 0.10–0.45
top-right:    x = 0.55–0.95, y = 0.10–0.45
bottom-left:  x = 0.05–0.45, y = 0.55–0.90
bottom-right: x = 0.55–0.95, y = 0.55–0.90
```

For each region, pixels are averaged in RGB space and the mean color is converted to HSV. Regions with saturation below 0.2 are omitted. Each retained normalized hue is matched by circular distance to the nearest reference hue in `{0, 1/3, 2/3}`. For measured hue `h_m` and matched reference `h_r`, the signed circular difference is:

```text
Δh = ((h_m − h_r + 0.5) mod 1) − 0.5
```

The calibration shift is the arithmetic mean of the retained `Δh` values. At least one sampling region must have saturation greater than or equal to 0.2. Measured patch hues, saturations, matched references, bounding box, and final shift are stored in `summary.json`.

## Phase-index mapping

The selected BGR video frame is converted to normalized RGB and then HSV. For each pixel, normalized hue `h0` is corrected by:

```text
h = (h0 − hue_shift) mod 1
```

Circular distance is:

```text
d_circular(a,b) = min(|a−b|, 1−|a−b|)
```

The fixed reference centers are:

```text
h_oil   = 0.110
h_water = 0.465
```

For every pixel in `M_final`, FLUID-Space calculates:

```text
d_oil   = d_circular(h, h_oil)
d_water = d_circular(h, h_water)
P       = 1 + d_water / (d_oil + d_water + ε)
```

where `ε` is the float32 machine epsilon used to prevent division by zero. `P` approaches 1 at the water reference and 2 at the oil reference. Pixels outside `M_final` are stored as `NaN`.

The index is a calibrated hue-distance index. It must not be described as volume fraction, concentration, saturation, or holdup unless the relationship has been independently validated for the complete optical and fluid system.

## Longitudinal statistics and direction

For each image column, the program reports the arithmetic mean of valid phase-index pixels and the valid-pixel count. The cumulative value at column `x` is the valid-pixel-weighted mean from the first valid flow-oriented column through `x`. When **Reverse result direction** is enabled, phase and mask crops are flipped horizontally before generating the longitudinal graph. The final cumulative value equals the mean of all valid phase-index pixels.

Low-saturation pixels are included in the primary analysis. Pixel counts below saturation thresholds 0.05, 0.10, and 0.15 are recorded as quality-control indicators.

## Exported data and quality control

Each run exports:

- Raw phase-index and valid-mask NumPy arrays in original image coordinates
- A flow-oriented cropped phase array
- Wet, exclusion, and final-mask QC images
- A phase-color QC image and optional CAD-line overlay
- A flow-oriented phase map
- Longitudinal column-mean, cumulative-mean, and valid-pixel-count graph
- JSON provenance and a compact CSV summary

Before accepting a run, inspect the selected frame, profile identity, final mask, calibration placement, bubble exclusions, phase-color image, low-saturation counts, and flow orientation. Preserve the complete run directory with the software version, DOI or repository release URL, and input-video hash.

## Manuscript-ready template

> A representative frame (frame [FRAME_NUMBER], time [TIME_S] s) was extracted from each experiment video ([WIDTH] × [HEIGHT] pixels; [FRAME_RATE] frames s−1) and analyzed using FLUID-Space v2.0.1 ([DOI]). Each analysis setup was stored as an independent profile containing an Interest Zone, Analysis ROI, Calibration ROI, bubble exclusions, and flow direction. The analysis geometry was defined as the intersection of the Interest Zone and Analysis ROI [and the registered CAD interior, for legacy-CAD profiles]. Calibration and manually annotated bubble regions were excluded. Mean RGB values from a 2×2 color swatch were converted to HSV; saturated patches were matched to circular reference hues 0, 1/3, and 2/3 to estimate a hue correction shift. Corrected hue was mapped using circular distances to fixed water (`h = 0.465`) and oil (`h = 0.110`) reference centers, producing a phase index from approximately 1 (water reference) to 2 (oil reference). Phase maps, masks, column-wise means, valid-pixel counts, cumulative valid-pixel-weighted indices, calibration measurements, and provenance hashes were exported. Low-saturation pixel counts were reviewed at `S = 0.05`, `0.10`, and `0.15`, and all masks and quality-control images were visually inspected before statistical analysis.

## Required study-specific reporting

Report the FLUID-Space version and DOI, profile name, frame-selection rule, video acquisition settings, pixel dimensions, frame rate, lighting, camera, dyes or tracers, fluid identities, calibration target, ROI/CAD mode, flow-direction convention, bubble-annotation procedure, run exclusion criteria, downstream statistical endpoint, and any independent validation used to interpret the phase index physically.
