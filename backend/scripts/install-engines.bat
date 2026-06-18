@echo off
echo Installing CodeReview analysis engines...
cd /d "%~dp0.."

echo.
echo [1/2] Installing Python linter (Ruff)...
call venv\Scripts\activate.bat 2>nul
pip install ruff>=0.9.6 -q
pip install -r requirements.txt -q

echo.
echo [2/2] Installing JavaScript linter (ESLint)...
cd tools\eslint-runner
call npm install
cd ..\..

echo.
echo Done! Restart backend with: uvicorn app.main:app --reload --port 8000
