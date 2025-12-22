@echo off
REM Parent Validator Backend - Quick Start
REM Uruchamia Flask backend na porcie 5000

echo.
echo ========================================
echo  Parent Validator Backend
echo ========================================
echo.

cd /d "%~dp0"

echo Sprawdzanie Pythona...
python --version
if errorlevel 1 (
    echo BŁĄD: Python nie jest zainstalowany!
    pause
    exit /b 1
)

echo.
echo Sprawdzanie Flask...
pip show flask >nul 2>&1
if errorlevel 1 (
    echo Flask nie jest zainstalowany. Instaluję...
    pip install flask flask-cors
)

echo.
echo ========================================
echo  Uruchamiam backend...
echo ========================================
echo.
echo Dostępne pod:
echo   - http://localhost:5000/api/health
echo   - http://127.0.0.1:5000/api/health
echo.
echo Naciśnij Ctrl+C aby zatrzymać
echo ========================================
echo.

python backend.py

pause
