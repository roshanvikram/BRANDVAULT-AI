@echo off
color 0A
echo.
echo  =======================================================
echo               BRANDVAULT AI // LAUNCHER
echo  =======================================================
echo.

cd /d "c:\Users\Roshan\Project\BRANDVAULT AI"

echo  [1/2] Launching Backend Server on http://127.0.0.1:8000 ...
start "BrandVault-Backend" cmd /k "cd /d c:\Users\Roshan\Project\BRANDVAULT AI && .\backend\venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000"

ping 127.0.0.1 -n 3 >nul

echo  [2/2] Launching Frontend Server on http://localhost:3000 ...
start "BrandVault-Frontend" cmd /k "cd /d c:\Users\Roshan\Project\BRANDVAULT AI\frontend && npm run dev"

ping 127.0.0.1 -n 4 >nul

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
echo  Keep those windows open while using the application.
