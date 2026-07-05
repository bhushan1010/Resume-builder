@echo off
echo Starting Resume Builder...

rem Resolve repo root (this script lives in scripts\dev\)
set "ROOT=%~dp0..\.."

echo Starting Backend Server...
start "Resume Builder Backend" cmd /k "cd /d "%ROOT%" && call venv\Scripts\activate && cd backend && uvicorn main:app --reload"

echo Starting Frontend Server...
start "Resume Builder Frontend" cmd /k "cd /d "%ROOT%\frontend" && npm run dev"

echo.
echo Both servers have been launched in separate terminal windows!
echo - Backend API is running at http://localhost:8000
echo - Frontend Web is running at http://localhost:5173
echo.
echo You can close this window now. The servers will keep running in their respective windows.
