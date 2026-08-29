@echo off
echo ===================================================
echo Starting PathWise AI (Backend + Frontend)
echo ===================================================

start "PathWise AI - Backend (Port 8000)" cmd /k "cd backend && .venv\Scripts\activate && python run.py"
start "PathWise AI - Frontend (Port 5173)" cmd /k "cd frontend && npm run dev"

echo.
echo Backend running at: http://localhost:8000
echo Frontend running at: http://localhost:5173
echo.
echo Login with:
echo   Email:    ganeshaidapu@gmail.com
echo   Password: password123
echo ===================================================
