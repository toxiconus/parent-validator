# 🚀 Parent Validator - Quick Start

**Walidator i edytor danych genealogicznych rodziców z polskich aktów chrztów**

---

## ⚡ 3 Kroki Do Uruchomienia

### 1. Uruchom Backend (opcjonalnie)
```bash
.\start-backend.bat
# Backend: http://localhost:5000
```

### 2. Otwórz UI
```
file:///J:/A.Gene/modules/data-entry/parent-validator/index.html
```

### 3. Załaduj Dane
- **Excel**: `Ctrl+C` → `Ctrl+V` → "Wczytaj dane"
- **Plik**: "Załaduj plik" → wybierz `.tsv`/`.csv`
- **Test**: "Załaduj z parsera" (5947 rekordów)

---

## 🎯 Co To Robi?

```
WEJŚCIE:
Excel z danymi:
  ID | Nazwisko | Imię | Rok | Ojciec | Matka
  
PRZETWORZENIE:
  → Parsowanie + walidacja z bazą 315 imion + 283 nazwisk
  → Kolorowanie: 🟢 OK / 🔴 Do sprawdzenia / ⚪ Brakujące
  
WYJŚCIE:
  → Edytowalna tabela + export TSV
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
