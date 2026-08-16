@echo off
setlocal
cd /d "%~dp0"
set "PYTHON_EXE=C:\ProgramData\anaconda3\python.exe"
if not exist "%PYTHON_EXE%" (
  echo Conda base Python was not found at %PYTHON_EXE%
  echo Run setup_env.bat, then edit PYTHON_EXE here if Conda is installed elsewhere.
  pause
  exit /b 1
)
"%PYTHON_EXE%" app.py --profile current_baseline
if errorlevel 1 pause
