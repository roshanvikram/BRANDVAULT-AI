@echo off
title BRANDVAULT AI — Startup
color 0A
echo.
echo  =============================================
echo   BRANDVAULT AI — Starting Services...
echo  =============================================
echo.

cd /d "c:\Users\Roshan\Project\BRANDVAULT AI"

echo  [1/3] Starting Backend API (Port 8000)...
start "BrandVault Backend" cmd /k "cd /d c:\Users\Roshan\Project\BRANDVAULT AI && .\backend\venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000"

timeout /t 2 /nobreak >nul

echo  [2/3] Building Frontend (this takes ~90 seconds)...
cd /d "c:\Users\Roshan\Project\BRANDVAULT AI\frontend"
call npm run build
if errorlevel 1 (
    echo.
    echo  ERROR: Frontend build failed! Check the output above.
    pause
    exit /b 1
)

echo.
echo  [3/3] Starting Frontend UI (Port 3000)...
start "BrandVault Frontend" cmd /k "cd /d c:\Users\Roshan\Project\BRANDVAULT AI\frontend && npm run start"

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
echo  Opening browser in 3 seconds...
timeout /t 3 /nobreak >nul
start "" "http://localhost:3000"

echo.
echo  Both windows are running. Keep them open!
echo  Press any key to close THIS window only.
pause >nul
