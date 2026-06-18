@echo off
echo Starting CodeReview Backend...
cd /d "%~dp0backend"
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
) else (
    echo Creating virtual environment...
    py -m venv venv 2>nul || python -m venv venv
    call venv\Scripts\activate.bat
    pip install -r requirements.txt
)
uvicorn app.main:app --reload --port 8000
