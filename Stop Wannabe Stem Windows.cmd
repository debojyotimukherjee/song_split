@echo off
setlocal

cd /d "%~dp0"
echo Stopping Wannabe Stem...

where docker >nul 2>nul
if errorlevel 1 (
  echo Docker is not installed or not on PATH.
  pause
  exit /b 1
)

docker compose down

echo.
echo Wannabe Stem stopped.
pause
