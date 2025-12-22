# 🚀 Parent Validator - Quick Start

**Walidator i edytor danych genealogicznych rodziców z polskich aktów chrztów**

---

## ⚡ 3 Kroki Do Uruchomienia

### 1. Uruchom Wszystko Razem
```bash
.\start-all-local.bat
# Frontend: http://localhost:8080/modules/data-entry/parent-validator/index.html
# Backend:  http://localhost:5000/api/health
```

### 2. Lub Osobno
```bash
# Backend (Python Flask)
.\start-backend.bat

# Frontend (statyczny HTML)
# Otwórz index.html w przeglądarce
```

### 3. Załaduj Dane
- **Excel**: `Ctrl+C` → `Ctrl+V` → "Wczytaj dane z pola"
- **Plik**: Przeciągnij lub wybierz `.tsv`/`.csv`/`.txt`
- **Test**: "Załaduj z parsera" (5947 rekordów z akt chrztów)

---

## 🏗️ Architektura

```
Frontend (HTML/JS) ←→ Backend (Python Flask)
       ↓                    ↓
   Walidacja JS        Parser Python + AI
   Tabela edycji       Baza imion/nazwisk
   Export TSV          Eksport JSON/TSV
```

**Backend Python:**
- Parser `parser_v2.py` obsługuje 5 formatów danych
- Walidacja z bazami: 315 imion + 283 nazwisk
- API REST: 
  - `/api/health` - status serwera
  - `/api/parse` - parsowanie danych
  - `/api/validate` - walidacja rekordów
  - `/api/table` - generowanie HTML tabeli
  - `/api/export/tsv` - eksport danych

---

## 🎯 Co To Robi?

```
WEJŚCIE:
Excel z danymi rodziców z akt chrztów
  
PRZETWORZENIE:
  → Inteligentne parsowanie (backend Python)
  → Walidacja imion/nazwisk z bazami danych
  → Kolorowanie: 🟢 OK / 🔴 Do sprawdzenia / ⚪ Brakujące
  
WYJŚCIE:
  → Edytowalna tabela + export TSV/JSON
```

---

## 📖 Pełna Dokumentacja

➡️ **[DOKUMENTACJA.md](DOKUMENTACJA.md)** - Kompletny przewodnik  
  (architektura, format danych, edycja, troubleshooting)

---

## 🐛 Szybkie Fix

```bash
# Backend nie startuje?
pip install flask flask-cors

# Port zajęty?
# backend.py: zmień port 5000 → 5001
```

---

**Last Updated**: 21 grudnia 2025
