@echo off
cd /d "%~dp0.."
where py >nul 2>nul || (echo Install Python 3.12 first. & exit /b 1)
where npm >nul 2>nul || (echo Install Node.js LTS, then reopen Command Prompt. & exit /b 1)
if not exist .venv\Scripts\python.exe py -3.12 -m venv .venv
if errorlevel 1 exit /b 1
.venv\Scripts\python.exe -m pip install -r eval\requirements.txt
if errorlevel 1 exit /b 1
.venv\Scripts\python.exe -m playwright install chromium
if errorlevel 1 (echo Browser download failed. Ask campus IT about download policies and trusted certificates. TLS must stay enabled. & exit /b 1)
call npm ci --prefix extension
if errorlevel 1 exit /b 1
call npm run build
if errorlevel 1 exit /b 1
set PYTHONPATH=%CD%\eval
.venv\Scripts\python.exe -m parallax.diagnose
echo Setup finished. Run scripts\run-smoke.cmd next.
