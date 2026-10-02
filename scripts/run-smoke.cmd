@echo off
cd /d "%~dp0.."
set PYTHONPATH=%CD%\eval
.venv\Scripts\python.exe -m parallax.smoke
if errorlevel 1 exit /b 1
.venv\Scripts\python.exe -m parallax.run --manifest data\smoke-manifest.jsonl
if errorlevel 1 exit /b 1
.venv\Scripts\python.exe -m parallax.evaluate
echo Results are saved under data\runs. Open scripts\dashboard.cmd.
