@echo off
REM Double-click launcher: switch to this folder and run Streamlit
REM with the Python interpreter inside .venv (no manual activation needed).
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo ERROR: .venv not found in this folder.
    echo Create it first:  py -3.13 -m venv .venv
    echo Then install deps: .\.venv\Scripts\python.exe -m pip install -r requirements.txt
    pause
    exit /b 1
)

.\.venv\Scripts\python.exe -m streamlit run app.py

pause
