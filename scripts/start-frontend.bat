@echo off
echo Starting CodeReview Frontend...
cd /d "%~dp0..\frontend"
call npm run dev
