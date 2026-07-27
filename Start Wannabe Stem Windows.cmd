@echo off
setlocal

cd /d "%~dp0"
echo Starting Wannabe Stem...
echo.

where docker >nul 2>nul
if errorlevel 1 (
  echo Docker Desktop is not installed.
  echo Install it from https://www.docker.com/products/docker-desktop/ and run this again.
  pause
  exit /b 1
)

docker info >nul 2>nul
if errorlevel 1 (
  echo Waiting for Docker Desktop...
  if exist "%ProgramFiles%\Docker\Docker\Docker Desktop.exe" (
    start "" "%ProgramFiles%\Docker\Docker\Docker Desktop.exe"
  )
)

set /a ATTEMPT=0
:wait_for_docker
docker info >nul 2>nul
if not errorlevel 1 goto docker_ready
set /a ATTEMPT+=1
if %ATTEMPT% GEQ 90 (
  echo Docker Desktop did not become ready. Open Docker Desktop and try again.
  pause
  exit /b 1
)
timeout /t 2 /nobreak >nul
goto wait_for_docker

:docker_ready
if not exist data mkdir data
if not exist data\inbox mkdir data\inbox
if not exist data\jobs mkdir data\jobs
if not exist data\models mkdir data\models

set INSTALL_DEMUCS=true
docker compose up -d --build api
if errorlevel 1 (
  echo Wannabe Stem could not start.
  pause
  exit /b 1
)

echo.
echo Wannabe Stem is running.
echo Opening http://localhost:8000 ...
start "" "http://localhost:8000"
echo.
echo You can close this window. Use Stop Wannabe Stem Windows.cmd when finished.
pause
