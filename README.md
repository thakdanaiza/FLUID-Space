# FLUID-Space

FLUID-Space creates CAD-authoritative phase maps. The operator only edits:

- Interest Zone for CH1 and CH2
- ROI for CH1-1, CH1-2, CH2-1 and CH2-2
- Bubble exclusions for each channel
- Source video and analysis frame for each profile

CAD placement, CAD outlines, internal islands and calibration are locked baseline assets. The final analysis area is:

```text
CAD interior ∩ Channel ROI ∩ Interest Zone − Bubble exclusions
```

No Conda installation is required. FLUID-Space uses a private Python virtual environment named `.venv` inside the project folder.

## Quick installation

**Windows:** Install Python 3.12 from Python.org, extract the ZIP and double-click `setup_env.bat` once. After setup, launch the application with `start_ui.bat`.

**macOS:** Install Python 3.12 from Python.org, extract the ZIP and run the following commands in Terminal:

```bash
cd "/path/to/FLUID-Space"
bash setup_env.sh
bash start_ui.sh
```

The setup script creates `.venv` and installs all required packages automatically. It does not require Conda or modify other Python environments on the computer.

## What to send to another user

On Windows, double-click `make_release.bat`. On macOS, run `bash make_release.sh`. The ready-to-send ZIP will be created in `releases/`.

The release tool includes the complete application but excludes generated folders:

```text
.venv/
__pycache__/
profiles/*/.generated/
profiles/*/runs/
```

Keep `profiles/current_baseline/profile.json` in the ZIP. It contains the approved Interest Zones, ROIs and Bubble setup.
Videos selected in the UI are copied into the matching profile folder and are included in the release ZIP automatically. Large source videos will increase the ZIP size.

The receiver should extract the ZIP to a normal writable folder such as Documents. Do not run the application directly from inside the ZIP.

## Requirements

- Windows 10/11 64-bit, or a current Intel/Apple Silicon macOS
- Python 3.12 recommended (Python 3.11–3.13 supported by the setup scripts)
- Internet access during the first setup only
- Approximately 1 GB free disk space for Python packages and generated results

Download Python from the official site:

- Windows: <https://www.python.org/downloads/windows/>
- macOS: <https://www.python.org/downloads/macos/>

The official macOS `universal2` installer works on both Intel and Apple Silicon Macs. On Windows, enable the option that makes Python available from the command line when the installer offers it.

## Windows installation

1. Install Python 3.12 (64-bit).
2. Extract the FLUID-Space ZIP.
3. Double-click `setup_env.bat` once.
4. Wait until `Environment check passed` is shown.
5. Double-click `start_ui.bat` whenever you want to use the program.

`start_ui.bat` also runs the setup automatically when `.venv` does not exist.

To run the current profile without opening the editor, double-click `run_current_profile.bat`.

## macOS installation

Install Python 3.12 using the official macOS installer, then open Terminal and run:

```bash
cd "/path/to/FLUID-Space"
bash setup_env.sh
bash start_ui.sh
```

Replace `/path/to/FLUID-Space` with the extracted folder path. A quick way to enter the correct path is to type `cd ` and drag the FLUID-Space folder into the Terminal window.

After the first setup, launch the UI with:

```bash
cd "/path/to/FLUID-Space"
bash start_ui.sh
```

Optional Finder launcher:

```bash
chmod +x start_ui_mac.command
```

After that, `start_ui_mac.command` can be opened from Finder. If macOS asks for confirmation because the file came from another computer, use Finder's **Open** command and review the prompt normally.

To run the current profile without opening the editor:

```bash
bash run_current_profile.sh
```

## Using the UI

1. Select or duplicate a profile.
2. Under **Source video**, press **Select video…**. FLUID-Space validates its resolution, copies it into the profile, and binds it to that profile.
3. Enter the analysis frame number and press **Load**.
4. Select a channel: CH1-1, CH1-2, CH2-1 or CH2-2.
5. Select `Interest Zone`, `Channel ROI` or `Bubble`.
6. Draw or adjust the geometry.
7. Press **Save** or **Run result**.

Drawing controls:

- Left click: add a point
- Right click or Enter: close the polygon
- Mouse wheel: zoom
- Middle-button drag: pan
- Esc: cancel the current draft
- Ctrl+S: save

Use **Duplicate as…** before creating a new setup. This keeps `current_baseline` available as the approved reference profile. If the source profile has its own copied video, the duplicate receives its own copy so that the two profiles remain independent.

The selected video path, original filename, frame number, FPS and frame count are stored with the profile. **Run result** always uses the video bound to the active profile; it does not silently fall back to a different video.

## Results

Each profile stores its own runs under `profiles/<profile-name>/runs/run_xxx/`.

The main publication image is `graphs/phase_publication_aligned_left.png`. The PDF, masks, arrays, QC images and summaries are stored in the same run folder.

## Manual terminal commands

Windows PowerShell:

```powershell
.\.venv\Scripts\python.exe app.py --check
.\.venv\Scripts\python.exe run_profile.py --profile current_baseline --check
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

macOS Terminal:

```bash
./.venv/bin/python app.py --check
./.venv/bin/python run_profile.py --profile current_baseline --check
./.venv/bin/python -m unittest discover -s tests -v
```

## Troubleshooting

### Python was not found

Install Python 3.12 from Python.org, close all Terminal or Command Prompt windows, reopen them and run the setup again.

### Tkinter is missing on macOS

Run `python3 -m tkinter`. If no small Tk window opens, install the official Python.org macOS package and recreate `.venv` with:

```bash
bash setup_env.sh --recreate
```

### A package installation fails

Confirm that the computer has internet access, then run the setup script again. The setup is safe to rerun and updates only the project's `.venv`.

### Reset the local environment

Windows:

```text
setup_env.bat --recreate
```

macOS:

```bash
bash setup_env.sh --recreate
```

This removes and recreates `.venv` only. Profiles and results are not removed.
