@echo off
title Parent Validator - Uruchamianie

echo ========================================
echo 🚀 Parent Validator Launcher
echo ========================================
echo.

REM Pobierz ścieżkę do katalogu głównego A.Gene
for %%I in ("%~dp0..\..\..") do set "ROOT_DIR=%%~fI"

echo 📁 Katalog główny: %ROOT_DIR%
echo.

REM Uruchom backend w tle
echo 🔧 Uruchamiam backend Python...
start /B python backend.py

REM Poczekaj chwilę na uruchomienie backendu
timeout /t 3 /nobreak >nul

REM Uruchom frontend server w tle w katalogu głównym
echo 🌐 Uruchamiam frontend server...
start /B /D "%ROOT_DIR%" python -m http.server 8080

REM Poczekaj na uruchomienie serwerów
echo ⏳ Czekam na serwery...
timeout /t 5 /nobreak >nul

REM Otwórz stronę w przeglądarce
echo 🌍 Otwieram stronę w przeglądarce...
start http://localhost:8080/modules/data-entry/parent-validator/index.html

echo.
echo ========================================
echo ✅ Aplikacja uruchomiona!
echo ========================================
echo 🌐 Frontend: http://localhost:8080/modules/data-entry/parent-validator/index.html
echo 🔧 Backend:  http://localhost:5000/api/health
echo ========================================
echo.
echo 💡 Serwery działają w tle
echo 💡 Zamknij okna CMD, aby zatrzymać serwery
echo.

pause