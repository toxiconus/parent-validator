@echo off
setlocal enabledelayedexpansion
title A.Gene Parent Validator Launcher

REM Pobierz ścieżkę skryptu (bez trailing backslash)
for %%I in ("%~dp0.") do set "SCRIPT_DIR=%%~fI"
for %%I in ("%SCRIPT_DIR%\..\..\..") do set "ROOT=%%~fI"

echo SCRIPT_DIR: %SCRIPT_DIR%
echo ROOT: %ROOT%

REM Serwer statyczny (port 8080) z katalogu głównego A.Gene
start "Frontend Server" cmd /k "cd /d "%ROOT%" && python -m http.server 8080"

REM Backend parent-validator (port 5000) z folderu modułu
start "Backend Server" cmd /k "cd /d "%SCRIPT_DIR%" && python backend.py"

echo.
echo ========================================
echo  Serwery uruchomione!
echo ========================================
echo  Frontend: http://localhost:8080/modules/data-entry/parent-validator/index.html
echo  Backend:  http://localhost:5000/api/health
echo ========================================
echo.

endlocal
