# FLUID-Space v2.0.1 Reproducibility Record

## Reference implementation

- Release: `v2.0.1`
- Repository: <https://github.com/thakdanaiza/FLUID-Space>
- DOI: <https://doi.org/10.5281/zenodo.22888466>
- Release date: 2026-09-22
- Operating system tested: Windows 11 (`10.0.26200`)
- Python: 3.12.7
- NumPy: 1.26.4
- OpenCV (`opencv-python-headless`): 4.14.0.94
- Matplotlib: 3.9.2
- Pillow: 10.4.0

`environment.yml` records the tested dependency versions. `requirements.txt` retains supported version ranges for ordinary installation.

## Reproduce the included baseline check

```powershell
conda env create -f environment.yml
conda activate fluid-space
python -m unittest discover -s tests -v
python run_profile.py --profile current_baseline_CH1-1 --check
```

The check reads `assets/reference.mp4`, frame 120, through the migrated `current_baseline_CH1-1` profile without creating an analysis run directory.

## Run provenance

Every completed analysis writes `summary.json`, including the profile, selected frame, input-video SHA-256, geometry mode, flow orientation, calibration measurements, mask pixel counts, low-saturation counts, phase statistics, and crop bounds. SHA-256 values for the Windows and macOS packages are published as `FLUID-Space-v2.0.1-SHA256SUMS.txt` in the GitHub Release and should be retained with the software version or DOI.

## Scientific interpretation

The reported phase index is a calibrated hue-distance index. It is not inherently a volume fraction, concentration, saturation, or holdup. Those interpretations require independent validation for the complete optical and fluid system.
