@echo off
echo ============================================
echo   InsightFlow - Starting All Services
echo ============================================
echo.

echo [1/2] Starting Backend (FastAPI) on port 8000...
start "InsightFlow Backend" cmd /k "cd /d %~dp0backend && python run.py"
timeout /t 3 /nobreak >nul

echo [2/2] Starting Frontend (Next.js) on port 3000...
start "InsightFlow Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo ============================================
echo   InsightFlow is starting up!
echo   Backend:  http://localhost:8000
echo   Frontend: http://localhost:3000
echo   API Docs: http://localhost:8000/docs
echo ============================================
echo.
pause
