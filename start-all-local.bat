@echo off
setlocal enabledelayedexpansion
title A.Gene Parent Validator Launcher

REM Pobierz ścieżkę skryptu (bez trailing backslash)
for %%I in ("%~dp0.") do set "SCRIPT_DIR=%%~fI"
for %%I in ("%SCRIPT_DIR%\..\..\..") do set "ROOT=%%~fI"

echo ========================================
echo   A.Gene Parent Validator Launcher
echo ========================================
echo SCRIPT_DIR: %SCRIPT_DIR%
echo ROOT: %ROOT%
echo.

REM Sprawdź czy porty są wolne
echo 🔍 Sprawdzam porty...
netstat -ano | findstr ":8080" >nul
if %errorlevel% equ 0 (
    echo ⚠️  Port 8080 zajęty - zatrzymuję stary proces...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8080"') do (
        taskkill /PID %%a /F >nul 2>&1
    )
)

netstat -ano | findstr ":5000" >nul
if %errorlevel% equ 0 (
    echo ⚠️  Port 5000 zajęty - zatrzymuję stary proces...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5000"') do (
        taskkill /PID %%a /F >nul 2>&1
    )
)

echo ✅ Porty wolne
echo.

REM Backend parent-validator (port 5000) - uruchom PIERWSZY
echo 🔧 Uruchamiam Backend Server (port 5000)...
start "Parent Validator Backend" cmd /k "cd /d "%SCRIPT_DIR%" && python backend.py"

REM Poczekaj na backend
timeout /t 3 /nobreak >nul

REM Serwer statyczny (port 8080)
echo 🌐 Uruchamiam Frontend Server (port 8080)...
start "Frontend Static Server" cmd /k "cd /d "%ROOT%" && python -m http.server 8080 --bind 0.0.0.0"

REM Poczekaj na uruchomienie serwerów
echo ⏳ Czekam na pełne uruchomienie serwerów...
timeout /t 5 /nobreak >nul

REM Sprawdź czy serwery działają
echo.
echo 🔍 Sprawdzam dostępność serwerów...
echo.

powershell -Command "& {try { $null = Invoke-WebRequest -Uri 'http://localhost:5000/api/health' -TimeoutSec 10 -UseBasicParsing; Write-Host '✅ Backend OK (http://localhost:5000)' -ForegroundColor Green } catch { Write-Host '❌ Backend niedostępny' -ForegroundColor Red }}"

powershell -Command "& {try { $null = Invoke-WebRequest -Uri 'http://10.42.163.151:5000/api/health' -TimeoutSec 10 -UseBasicParsing; Write-Host '✅ Backend OK (http://10.42.163.151:5000)' -ForegroundColor Green } catch { Write-Host '❌ Backend niedostępny w sieci' -ForegroundColor Yellow }}"

powershell -Command "& {try { $null = Invoke-WebRequest -Uri 'http://localhost:8080/modules/data-entry/parent-validator/index.html' -TimeoutSec 10 -UseBasicParsing; Write-Host '✅ Frontend OK (http://localhost:8080)' -ForegroundColor Green } catch { Write-Host '❌ Frontend niedostępny' -ForegroundColor Yellow }}"

powershell -Command "& {try { $null = Invoke-WebRequest -Uri 'http://10.42.163.151:8080/modules/data-entry/parent-validator/index.html' -TimeoutSec 10 -UseBasicParsing; Write-Host '✅ Frontend OK (http://10.42.163.151:8080)' -ForegroundColor Green } catch { Write-Host '❌ Frontend niedostępny w sieci' -ForegroundColor Yellow }}"

echo.
echo ========================================
echo   🎉 Serwery uruchomione!
echo ========================================
echo 🌐 Aplikacja lokalnie: http://localhost:8080/modules/data-entry/parent-validator/index.html
echo 🌐 Aplikacja w sieci: http://10.42.163.151:8080/modules/data-entry/parent-validator/index.html
echo 🔧 Backend API lokalnie: http://localhost:5000/api/health
echo 🔧 Backend API w sieci: http://10.42.163.151:5000/api/health
echo ========================================
echo.

REM Otwórz stronę w domyślnej przeglądarce
echo 🌍 Otwieram aplikację w przeglądarce...
timeout /t 2 /nobreak >nul
start http://localhost:8080/modules/data-entry/parent-validator/index.html

echo.
echo 💡 Serwery działają w tle w osobnych oknach
echo 💡 Zamknij te okna aby zatrzymać serwery
echo 💡 To okno możesz zamknąć
echo.
echo Naciśnij dowolny klawisz aby zamknąć to okno...
pause >nul

endlocal
