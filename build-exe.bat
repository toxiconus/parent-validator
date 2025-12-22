@echo off
setlocal enabledelayedexpansion
title Budowanie Parent Validator Launcher EXE

echo ========================================
echo Budowanie Parent Validator Launcher EXE
echo ========================================
echo.

REM Sprawdź czy PyInstaller jest zainstalowany
"C:\Users\toxic\AppData\Roaming\Python\Python313\python.exe" -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo ❌ PyInstaller nie jest zainstalowany
    echo Instaluję PyInstaller...
    "C:\Users\toxic\AppData\Roaming\Python\Python313\python.exe" -m pip install pyinstaller
    if errorlevel 1 (
        echo ❌ Błąd instalacji PyInstaller
        pause
        exit /b 1
    )
)

echo ✅ PyInstaller jest dostępny
echo.

REM Zbuduj EXE
echo 🚀 Buduję plik EXE...
"C:\Users\toxic\AppData\Roaming\Python\Python313\python.exe" -m pyinstaller --clean --onefile launcher.spec

if errorlevel 1 (
    echo ❌ Błąd podczas budowania EXE
    pause
    exit /b 1
)

echo.
echo ✅ Plik EXE został utworzony!
echo 📁 Lokalizacja: dist\ParentValidatorLauncher.exe
echo.

REM Sprawdź czy plik istnieje
if exist "dist\ParentValidatorLauncher.exe" (
    echo ✅ Plik EXE jest gotowy do użycia
    echo 💡 Możesz go skopiować gdziekolwiek i uruchomić
) else (
    echo ❌ Plik EXE nie został znaleziony
)

echo.
echo ========================================
pause