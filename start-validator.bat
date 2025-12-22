@echo off
echo ========================================
echo Parent Validator - Local Server
echo ========================================
echo.
echo Uruchamiam lokalny serwer HTTP...
echo Strona bedzie dostepna na: http://localhost:8080
echo.
echo Aby zatrzymac serwer, nacisnij Ctrl+C
echo ========================================
echo.

cd /d "%~dp0"
python -m http.server 8080
