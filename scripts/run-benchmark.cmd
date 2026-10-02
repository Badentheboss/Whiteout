@echo off
cd /d "%~dp0.."
set PYTHONPATH=%CD%\eval
.venv\Scripts\python.exe -m parallax.run %*
if errorlevel 1 exit /b 1
.venv\Scripts\python.exe -m parallax.evaluate
