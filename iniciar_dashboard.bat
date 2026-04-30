@echo off
cd /d %~dp0
.venv\Scripts\python -m streamlit run dashboard/app.py
pause