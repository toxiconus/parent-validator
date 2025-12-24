# 📘 Parent Validator - Dokumentacja

**Wersja**: 2.1 (22 grudnia 2025)  
**Port Backend**: http://localhost:5000 (opcjonalny)

---

## 🎯 CEL

Edycja, walidacja i poprawianie danych genealogicznych rodziców z polskich aktów chrztów (1783-1862).
- Podział danych rodziców na pola: imię ojca, nazwisko ojca, imię matki, nazwisko matki
- Walidacja względem bazy 315 imion + 283 nazwisk
- Kolorowanie: 🟢 OK / 🔴 Do sprawdzenia / ⚪ Brakujące

---

## 🚀 URUCHOMIENIE

1. **Backend (opcjonalnie)**: `start-backend.bat`
2. **UI**: Otwórz `index.html` w przeglądarce
3. **Załaduj dane**: Ctrl+V z Excel / Upload TSV/CSV / Przykłady

---

## 📊 STRUKTURA PLIKÓW

### Frontend:
- `index.html` - UI
- `parent-validator.js` - Logika aplikacji
- `parent-validator.css` - Style
- `edit-modal.html` / `edit-modal.css` - Modal edycji

### Backend:
- `backend.py` - Flask API
- `parser_v2.py` - Python parser

### Dane:
- `../../../data/imiona_*.json` - Bazy imion
- `../../../data/nazwiska_*.json` - Bazy nazwisk

---

## 📝 FORMAT DANYCH

### Kolumny TSV:
```
ID | ROK | Nr | Nazwisko | Imię | Miejscowość | 
ImięO | NazwiskoO | wiekO | IM | NM | wM | uwagi | UWAGI ORG
```

### Kolorowanie:
- **Zielony** - walidowane w bazie
- **Czerwony** - nieznalezione / do sprawdzenia
- **Szary** - puste

---

## ⌨️ SKRÓTY

- `Ctrl+V` - Wklej dane
- `Ctrl+O` - Otwórz plik
- `2x klik` - Otwórz modal edycji
- `unfold_less` - Ukryj panele (tryb max)

**Wewnętrzne pola (nie eksportowane):**
- **child_relation** - `s.` (syn) lub `c.` (córka) - wyciągane z uwag

### Struktura Rekordu (JavaScript):
```javascript
{
  id: "CH.LUB.BLIN.0001574",
  surname: "Zyśko",
  name: "Zofia",
  year: "1841",
  place: "Moczydła",
  fatherName: "Józef",
  fatherSurname: "Zyśko",
  fatherAge: "l.40",              // NOWE
  fatherBirthEst: "~ 1801",       // NOWE
  fatherOccupation: "",           // NOWE
  motherName: "Marianna",
  motherSurname: "Kasperek",
  motherMaidenName: "Kasperek",
  motherAge: "l.35",              // NOWE
  motherBirthEst: "~ 1806",       // NOWE
  motherOccupation: "",           // NOWE
  notes: "",
  original: "CH.LUB.BLIN.0001574\tZyśko\tZofia...",
  fatherNameValidated: true,
  fatherSurnameValidated: true,
  motherNameValidated: true,
  motherSurnameValidated: true
}
```

### 5 Rozpoznawanych Formatów (Parser v2):

#### **Format A** (1783-1796): Prosty Historyczny
```
ID | Nazwisko | Imię | Nr | Rok | Miejsce | Uwagi
CH.LUB.BLIN.0000001 | Barbarzak | Józef | 1 | 1783 | - | nr karty 1
```
7-9 kolumn, brak danych rodziców.

#### **Format B** (1826-1830): Pełny z Danymi Rodziców
```
ID | Nazwisko | Imię | Nr | Rok | Data | Miejsce | ImięO | NazwiskoO | WiekO | ~UrO | ImięM | NazwiskoM | WiekM | ~UrM
CH.LUB.BLIN.0000742 | Pyć | Paweł | 1 | 1826 | 2.01.1826 | Blinów | Wojciech | Pyć | 40 | ~ 1786 | Anastazja | Głaz | 30 | ~ 1796
```
15+ kolumn z pełnymi danymi (wiek, szacowane urodzenie).

#### **Format C** (1834-1839): Lista Bez Rodziców
```
ID | Nazwisko | Imię | Wiek | Rok | [puste]
CH.LUB.BLIN.0001199 | Kurczak | Franciszek | 15 | 1834
```
4-5 kolumn, tylko dane osoby.

#### **Format D** (1864-1899): Tekstowy Slash
```
ID | Nazwisko | Imię | Wiek | Rok | | Miejsce / Rodzice
CH.LUB.BLIN.0002999 | Kozyra | Jadwiga | 56 | 1864 | | Blinów / Piotr l.31 i Anna Zych l.34
```
Miejsce + rodzice w jednym polu tekstowym, parser automatycznie rozdziela.

#### **Format E**: Mieszany (specjalne przypadki)
```
s Andrzeja               → syn Andrzeja (tylko ojciec)
s. Katatzyny (wdowy)     → syn wdowy
c Michała i Rozalii      → córka obojga rodziców
z Marii niezamężnej      → matka niezamężna
```

### Specjalne Znaczniki (Zachowywane w Oryginalnej Formie):

| Znacznik | Znaczenie | Obsługa Parsera |
|----------|-----------|-----------------|
| `?` | Nieczytelne / do weryfikacji | Zachowywany, dodaje ostrzeżenie |
| `x` / `X` | Nie podano (brak danych) | Zachowywany, traktowany jako brak rodzica |
| `..` / `...` | Nieczytelne w oryginale | Zachowywany, oznacza jako "nieczytelne" |
| `-` | Nie dotyczy / puste | Zachowywany |
| `"brak aktu"` | Użytkownik nie widzi dokumentu | Przenoszone do uwag |

---

---

## 🎨 KOLOROWANIE STATUSU

