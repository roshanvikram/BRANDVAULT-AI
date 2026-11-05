@echo off
title BRANDVAULT AI — Launcher
color 0A
echo.
echo  =======================================================
echo               BRANDVAULT AI // LAUNCHER
echo  =======================================================
echo.

cd /d "c:\Users\Roshan\Project\BRANDVAULT AI"

echo  [1/2] Launching Backend Server on http://127.0.0.1:8000 ...
start "BrandVault-Backend" cmd /k "cd /d c:\Users\Roshan\Project\BRANDVAULT AI && .\backend\venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000"

timeout /t 2 /nobreak >nul

if not exist "c:\Users\Roshan\Project\BRANDVAULT AI\frontend\.next\BUILD_ID" (
    echo.
    echo  No build detected. Building frontend (takes ~60-90s)...
    cd /d "c:\Users\Roshan\Project\BRANDVAULT AI\frontend"
    call npm run build
)

echo.
echo  [2/2] Launching Frontend Server on http://localhost:3000 ...
start "BrandVault-Frontend" cmd /k "cd /d c:\Users\Roshan\Project\BRANDVAULT AI\frontend && npm run start"

timeout /t 3 /nobreak >nul

echo.
echo  =======================================================
echo               BRANDVAULT AI IS NOW ONLINE!
echo  =======================================================
echo.
echo   Frontend :  http://localhost:3000
echo   Backend  :  http://127.0.0.1:8000
echo   API Docs :  http://127.0.0.1:8000/docs
echo.
echo  Opening browser...
start "" "http://localhost:3000"

echo.
echo  Both services are running in background console windows.
echo  You may close this launcher window now.
pause >nul
