@echo off
cd /d "%~dp0.."
set PYTHONPATH=%CD%\eval
.venv\Scripts\python.exe -m streamlit run eval\parallax\dashboard.py --server.address 127.0.0.1
