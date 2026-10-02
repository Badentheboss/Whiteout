@echo off
cd /d "%~dp0.."
set PYTHONPATH=%CD%\eval
if not exist reviews mkdir reviews
.venv\Scripts\python.exe -m parallax.review sources --input data\research-manifest.jsonl --output reviews\sources-pending.jsonl
if errorlevel 1 exit /b 1
.venv\Scripts\python.exe -m parallax.review negatives --input data\hard-negatives.jsonl --output reviews\negatives-pending.jsonl --count 300
echo Pending forms only. No benchmark was started and no human labels were created.
