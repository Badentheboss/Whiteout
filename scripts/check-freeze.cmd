@echo off
cd /d "%~dp0.."
set PYTHONPATH=%CD%\eval
if "%~1"=="" (echo Usage: scripts\check-freeze.cmd path-to-lock.json & exit /b 1)
.venv\Scripts\python.exe -m parallax.freeze check --lock "%~1"
