@echo off
setlocal
cd /d "%~dp0"
where conda >nul 2>nul
if errorlevel 1 (
  echo Conda is not available on PATH.
  echo Open Anaconda Prompt and run: conda env create -f environment.yml
  pause
  exit /b 1
)
conda env create -f environment.yml
if errorlevel 1 (
  echo Environment creation failed.
  pause
  exit /b 1
)
echo Created Conda environment: fluid-space
pause
