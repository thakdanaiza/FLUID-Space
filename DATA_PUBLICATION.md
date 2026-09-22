# Publishing Research Profiles and Videos

FLUID-Space software and experiment data should be published as separate archival records:

1. **Software record** — created automatically by the Zenodo/GitHub integration from a GitHub Release such as `v2.0.1`.
2. **Dataset record** — uploaded manually to Zenodo and containing the selected profile JSON files, their bound videos, a manifest, checksums, and dataset documentation.

Keeping these records separate avoids placing large or study-specific videos in Git, permits an appropriate data license, and gives both the software and dataset independent DOIs.

## Prepare profiles locally

The recommended workflow is:

1. Open FLUID-Space.
2. Duplicate an existing profile and give it a study-safe name that contains no participant or confidential identifier.
3. Use **Select video…**. FLUID-Space copies the video into the profile and records a portable relative path.
4. Select the analysis frame, finish the geometry, save, and run `--check`.

The resulting local layout is:

```text
profiles/<profile-name>/profile.json
profiles/<profile-name>/source/<video-file>
```

These paths are intentionally ignored by Git, except for the bundled public baseline.

## Build a Zenodo dataset bundle

Choose a data license only after confirming that all contributors and the institution authorize publication of the videos. MIT applies to the software, not automatically to experiment data. `CC-BY-4.0` is a common choice when reuse with attribution is intended; `CC0-1.0` waives most rights; `All-Rights-Reserved` is restrictive.

Example:

```powershell
python tools/prepare_research_dataset.py `
  --title "TIGERS-X FLUID-Space analysis dataset" `
  --data-license CC-BY-4.0 `
  --profile experiment_a `
  --profile experiment_b
```

The command validates each profile and video, creates a portable profile/video layout, and writes a ZIP plus SHA-256 checksum under `releases/`. It does not modify the working profiles.

## Upload to Zenodo

Create a new upload manually and select resource type **Dataset**. Upload the generated dataset ZIP and its checksum file. Use the study's actual creators, title, description, keywords, access conditions, and data license. Add the FLUID-Space software DOI as a related identifier after Zenodo archives the software release. Then add the dataset DOI back to the paper and, if desired, to the repository documentation.

Before publishing, verify:

- The videos contain no personal, confidential, export-controlled, or third-party material.
- All creators and ISHA/Chulabhorn Royal Academy authorize public distribution.
- Profile names and video filenames do not expose sensitive identifiers.
- The selected license matches the consent and institutional policy.
- The dataset README states acquisition conditions, frame-selection rules, and the relationship between each profile and video.
- The generated SHA-256 checksum matches the uploaded ZIP.
