#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skrypt do budowania pliku EXE dla Parent Validator Launcher
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def main():
    print("=" * 60)
    print("🚀 Budowanie Parent Validator Launcher EXE")
    print("=" * 60)

    script_dir = Path(__file__).parent
    os.chdir(script_dir)

    # Sprawdź PyInstaller
    try:
        import PyInstaller
        print("✅ PyInstaller jest dostępny")
    except ImportError:
        print("❌ PyInstaller nie jest zainstalowany")
        print("Instaluję PyInstaller...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
            print("✅ PyInstaller zainstalowany")
        except subprocess.CalledProcessError:
            print("❌ Błąd instalacji PyInstaller")
            return 1

    # Zbuduj EXE
    print("🚀 Buduję plik EXE...")
    try:
        cmd = [sys.executable, "-m", "pyinstaller", "--clean", "--onefile", "launcher.spec"]
        subprocess.check_call(cmd)
        print("✅ Plik EXE został utworzony!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Błąd podczas budowania EXE: {e}")
        return 1

    # Sprawdź wynik
    exe_path = script_dir / "dist" / "ParentValidatorLauncher.exe"
    if exe_path.exists():
        print(f"✅ Plik EXE jest gotowy: {exe_path}")
        print("💡 Możesz go skopiować gdziekolwiek i uruchomić")
        print(f"📏 Rozmiar pliku: {exe_path.stat().st_size} bajtów")
    else:
        print("❌ Plik EXE nie został znaleziony")
        return 1

    print("=" * 60)
    return 0

if __name__ == "__main__":
    sys.exit(main())