@echo off
setlocal
cd /d "%~dp0"
set "PYTHON_EXE=C:\ProgramData\anaconda3\python.exe"
if not exist "%PYTHON_EXE%" (
  echo Conda base Python was not found at %PYTHON_EXE%
  pause
  exit /b 1
)
"%PYTHON_EXE%" run_profile.py --profile current_baseline
if errorlevel 1 (
  echo.
  echo Pipeline stopped. Review the error above.
  pause
  exit /b 1
)
echo.
echo Result completed under profiles\current_baseline\runs
pause
