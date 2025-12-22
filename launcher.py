#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Launcher dla Parent Validator - uruchamia frontend i backend oraz otwiera stronę
"""

import os
import sys
import subprocess
import time
import webbrowser
import threading
from pathlib import Path

def get_script_dir():
    """Pobierz katalog skryptu"""
    return Path(__file__).parent.absolute()

def get_root_dir():
    """Pobierz katalog główny A.Gene"""
    return get_script_dir().parent.parent.parent

def start_frontend_server(root_dir, port=8080):
    """Uruchom serwer frontend w tle"""
    try:
        print(f"🚀 Uruchamiam frontend server na porcie {port}...")
        cmd = [sys.executable, "-m", "http.server", str(port)]
        process = subprocess.Popen(
            cmd,
            cwd=str(root_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )
        print(f"✅ Frontend server uruchomiony (PID: {process.pid})")
        return process
    except Exception as e:
        print(f"❌ Błąd uruchamiania frontend server: {e}")
        return None

def start_backend_server(script_dir, port=5000):
    """Uruchom backend server w tle"""
    try:
        print(f"🚀 Uruchamiam backend server na porcie {port}...")
        cmd = [sys.executable, "backend.py"]
        process = subprocess.Popen(
            cmd,
            cwd=str(script_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )
        print(f"✅ Backend server uruchomiony (PID: {process.pid})")
        return process
    except Exception as e:
        print(f"❌ Błąd uruchamiania backend server: {e}")
        return None

def wait_for_servers(frontend_process, backend_process, timeout=10):
    """Poczekaj aż serwery będą gotowe"""
    print("⏳ Czekam na uruchomienie serwerów...")

    start_time = time.time()
    frontend_ready = False
    backend_ready = False

    while time.time() - start_time < timeout:
        if not frontend_ready and frontend_process.poll() is None:
            # Sprawdź czy frontend odpowiada
            try:
                import urllib.request
                urllib.request.urlopen("http://localhost:8080", timeout=1)
                frontend_ready = True
                print("✅ Frontend server gotowy")
            except:
                pass

        if not backend_ready and backend_process.poll() is None:
            # Sprawdź czy backend odpowiada
            try:
                import urllib.request
                urllib.request.urlopen("http://localhost:5000/api/health", timeout=1)
                backend_ready = True
                print("✅ Backend server gotowy")
            except:
                pass

        if frontend_ready and backend_ready:
            break

        time.sleep(0.5)

    return frontend_ready and backend_ready

def open_browser(url):
    """Otwórz stronę w przeglądarce"""
    print(f"🌐 Otwieram stronę: {url}")
    try:
        webbrowser.open(url)
        print("✅ Strona otwarta w przeglądarce")
    except Exception as e:
        print(f"❌ Błąd otwierania przeglądarki: {e}")

def main():
    print("=" * 60)
    print("🚀 A.Gene Parent Validator Launcher")
    print("=" * 60)

    # Pobierz ścieżki
    script_dir = get_script_dir()
    root_dir = get_root_dir()

    print(f"📁 Katalog skryptu: {script_dir}")
    print(f"📁 Katalog główny: {root_dir}")
    print()

    # Uruchom serwery
    frontend_process = start_frontend_server(root_dir, 8080)
    backend_process = start_backend_server(script_dir, 5000)

    if not frontend_process or not backend_process:
        print("❌ Nie udało się uruchomić serwerów")
        sys.exit(1)

    print()

    # Poczekaj na serwery
    servers_ready = wait_for_servers(frontend_process, backend_process, 15)

    if not servers_ready:
        print("⚠️  Serwery mogą nie być w pełni gotowe, ale próbuję otworzyć stronę...")

    print()
    print("=" * 60)
    print("🎉 Serwery uruchomione!")
    print("=" * 60)
    print("🌐 Frontend: http://localhost:8080/modules/data-entry/parent-validator/index.html")
    print("🔧 Backend:  http://localhost:5000/api/health")
    print("=" * 60)
    print()

    # Otwórz stronę
    frontend_url = "http://localhost:8080/modules/data-entry/parent-validator/index.html"
    open_browser(frontend_url)

    print()
    print("💡 Serwery działają w tle. Zamknij to okno, aby zatrzymać serwery.")
    print("💡 Możesz też zostawić otwarte dla dalszej pracy.")
    print()

    try:
        # Czekaj na zakończenie procesów lub przerwanie
        while True:
            if frontend_process.poll() is not None:
                print("⚠️  Frontend server zakończył pracę")
                break
            if backend_process.poll() is not None:
                print("⚠️  Backend server zakończył pracę")
                break
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Przerwano przez użytkownika")

    # Zatrzymaj serwery
    print("🛑 Zatrzymuję serwery...")
    try:
        frontend_process.terminate()
        backend_process.terminate()
        frontend_process.wait(timeout=5)
        backend_process.wait(timeout=5)
        print("✅ Serwery zatrzymane")
    except:
        try:
            frontend_process.kill()
            backend_process.kill()
        except:
            pass

    print("👋 Do widzenia!")

if __name__ == "__main__":
    main()