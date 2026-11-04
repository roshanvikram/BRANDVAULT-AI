@echo off
title BRANDVAULT AI — Startup
color 0A
echo.
echo  =============================================
echo   BRANDVAULT AI — Starting Services...
echo  =============================================
echo.

cd /d "c:\Users\Roshan\Project\BRANDVAULT AI"

echo  [1/2] Starting Backend API (Port 8000)...
start "BrandVault Backend" cmd /k "cd /d c:\Users\Roshan\Project\BRANDVAULT AI && .\backend\venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000"

timeout /t 3 /nobreak >nul

echo  [2/2] Starting Frontend UI (Port 3000)...
start "BrandVault Frontend" cmd /k "cd /d c:\Users\Roshan\Project\BRANDVAULT AI && npm run start --prefix frontend"

timeout /t 4 /nobreak >nul

echo.
echo  =============================================
echo   BRANDVAULT AI is LIVE!
echo  =============================================
echo.
echo   Frontend:   http://localhost:3000
echo   Backend:    http://127.0.0.1:8000
echo   API Docs:   http://127.0.0.1:8000/docs
echo.
echo  Opening browser...
start "" "http://localhost:3000"

echo.
echo  Press any key to close this window.
pause >nul

