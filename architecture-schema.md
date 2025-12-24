# Architektura Aplikacji - Schemat Wizualny

## 🏗️ **STRUKTURA APLIKACJI PO MIGRACJI**

```
┌─────────────────────────────────────────────────────────────────┐
│                    BROWSER (Frontend)                           │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                 APP STATE (Centralny Stan)              │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │  appState = {                                           │   │
│  │      records: [Record[]],    // Wszystkie dane          │   │
│  │      filters: {red,green,gray}, // Filtry wyświetlania  │   │
│  │      stats: {total,validated,warnings,empty}, // Staty │   │
│  │      currentRecord: Record,   // Dla modala             │   │
│  │      isLoading: boolean      // Status ładowania        │   │
│  │  }                                                      │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              UI COMPONENTS                              │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │   │
│  │  │   Input     │  │   Table     │  │   Modal     │      │   │
│  │  │  Textarea   │  │  (renderTable│  │   Edit      │      │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘      │   │
│  │                                                         │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │   │
│  │  │  Filters    │  │  Export     │  │  Stats      │      │   │
│  │  │  Buttons    │  │  Button     │  │  Display    │      │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘      │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              BUSINESS LOGIC                             │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │   │
│  │  │ validate-   │  │ update-     │  │ render-     │      │   │
│  │  │ RecordLocal │  │ Record      │  │ Table       │      │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘      │   │
│  │                                                         │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │   │
│  │  │ buildTSV    │  │ parseInput  │  │ calculate-  │      │   │
│  │  │             │  │             │  │ Stats       │      │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘      │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              DATA LAYER                                 │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │  nameDatabase = {                                       │   │
│  │      allNames: Set,                                     │   │
│  │      allSurnames: Set,                                  │   │
│  │      places: Set                                        │   │
│  │  }                                                      │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
               │
               │ HTTP Requests (tylko parsowanie)
               ▼
┌─────────────────────────────────────────────────────────────────┐
│                    BACKEND (Python/Flask)                       │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              API ENDPOINTS                              │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │   │
│  │  │ /api/parse  │  │ /api/vali-  │  │ /api/health │      │   │
│  │  │ (jednoraz.) │  │ date-field  │  │             │      │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘      │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              BUSINESS LOGIC                             │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │   │
│  │  │ Parser V2   │  │ Validator   │  │ Data Loader │      │   │
│  │  │ (advanced)  │  │             │  │             │      │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘      │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## 🔄 **PRZEPŁYW DANYCH - SEKWENCJA OPERACJI**

### **1. Wczytywanie danych:**
```
User Input → parseInput() → /api/parse → appState.records[] → renderTable()
```

### **2. Edycja rekordu:**
```
User Click → updateRecord() → validateRecordLocal() → renderTable()
```

### **3. Eksport danych:**
```
User Click → buildTSV() → Download File
```

---

## 📊 **STRUKTURA DANYCH - RECORD OBJECT**

```javascript
const Record = {
    // === DANE PODSTAWOWE ===
    id: "CH.LUB.BLIN.0001574",           // ID rekordu
    year: "1908",                        // Rok
    number: "001",                       // Numer aktu
    surname: "Zyśko",                    // Nazwisko dziecka
    name: "Zofia",                       // Imię dziecka
    place: "Bliżyn",                     // Miejscowość

    // === DANE RODZICÓW ===
    fatherName: "Józef",                 // Imię ojca
    fatherSurname: "Zyśko",              // Nazwisko ojca
    fatherAge: "40",                     // Wiek ojca
    motherName: "Maria",                 // Imię matki
    motherSurname: "Kowalska",           // Nazwisko matki
    motherAge: "35",                     // Wiek matki
    motherMaidenName: "Kowalska",        // Nazwisko panieńskie matki

    // === DANE SPECJALISTYCZNE ===
    recordType: "baptism",               // baptism | death | marriage
    recordTypeConfidence: "high",        // high | medium | low

    // === DANE DODATKOWE ===
    birthDate: "1908-01-15",             // Data urodzenia (chrzest)
    baptismDate: "1908-01-20",           // Data chrztu
    deathDate: "1950-03-10",             // Data zgonu
    marriageDate: "1930-06-15",          // Data ślubu

    // === METADANE WALIDACYJNE ===
    validation: {
        fatherName: { status: "valid", color: "green" },
        fatherSurname: { status: "valid", color: "green" },
        motherName: { status: "invalid", color: "red", suggestions: ["Maria", "Marya"] },
        motherSurname: { status: "valid", color: "green" },
        place: { status: "valid", color: "green" },
        fatherAge: { status: "warning", color: "orange", message: "Nietypowy wiek" }
    },

    // === KONTROLA ZMIAN ===
    isModified: false,                   // Czy rekord był edytowany
    originalText: "...",                 // Oryginalny tekst wejściowy
    changeHistory: [                     // Historia zmian dla undo/redo
        { field: "motherName", oldValue: "Marya", newValue: "Maria", timestamp: 1234567890 }
    ],

    // === UWAGI I NOTATKI ===
    notes: "Dodatkowe informacje",       // Uwagi użytkownika
    warnings: [],                        // Ostrzeżenia z parsowania
    suggestions: {}                      // Sugestie poprawek
};
```

---

## 🔧 **KLUCZOWE FUNKCJE - INTERFEJSY**

### **State Management:**
```javascript
// Centralne zarządzanie stanem
function updateRecord(recordId, field, value) {
    const record = appState.records.find(r => r.id === recordId);
    if (record) {
        // Zapisz do historii zmian
        record.changeHistory.push({
            field, oldValue: record[field], newValue: value,
            timestamp: Date.now()
        });

        // Aktualizuj wartość
        record[field] = value;
        record.isModified = true;

        // Walidacja lokalna
        validateRecordLocal(record);

        // Aktualizuj UI
        updateStats();
        renderTable();
    }
}
```

### **Local Validation:**
```javascript
function validateRecordLocal(record) {
    // Reset validation
    record.validation = {};

    // Validate each field
    const fields = ['fatherName', 'motherName', 'fatherSurname', 'motherSurname', 'place'];
    fields.forEach(field => {
        const value = record[field];
        if (!value) {
            record.validation[field] = { status: 'empty', color: 'gray' };
        } else {
            const isValid = validateField(field, value);
            record.validation[field] = {
                status: isValid ? 'valid' : 'invalid',
                color: isValid ? 'green' : 'red',
                suggestions: isValid ? [] : getSuggestions(field, value)
            };
        }
    });
}
```

### **Table Rendering:**
```javascript
function renderTable() {
    const tbody = document.getElementById('tableBody');
    tbody.innerHTML = '';

    // Filter records
    const visibleRecords = appState.records.filter(record => {
        const status = getRecordStatus(record);
        return appState.filters[status];
    });

    // Render each row
    visibleRecords.forEach(record => {
        tbody.appendChild(createTableRow(record));
    });

    // Update stats
    updateStatsDisplay();
}
```

---

## 🌐 **API ENDPOINTS - SPECYFIKACJA**

### **POST /api/parse**
**Cel:** Jednorazowe parsowanie surowych danych  
**Input:**
```json
{
    "data": "TSV content as string",
    "delimiter": "\t"
}
```
**Output:**
```json
{
    "success": true,
    "records": [
        {
            "id": "CH.LUB.BLIN.0001574",
            "recordType": "baptism",
            "recordTypeConfidence": "high",
            "validation": { /* ... */ },
            "suggestions": { /* ... */ },
            // ... full record object
        }
    ],
    "stats": {
        "parsed": 5947,
        "warnings": 23,
        "errors": 0
    }
}
```

### **POST /api/validate-field** *(opcjonalny)*
**Cel:** Walidacja pojedynczego pola z kontekstem  
**Input:**
```json
{
    "fieldType": "name",
    "value": "Józef",
    "context": {
        "recordType": "baptism",
        "year": "1908"
    }
}
```
**Output:**
```json
{
    "status": "valid",
    "color": "green",
    "suggestions": [],
    "confidence": 0.95
}
```

---

## 📈 **METRYKI WYDAJNOŚCI**

### **Cele wydajnościowe:**
- **Ładowanie:** < 2s dla 10k rekordów
- **Renderowanie tabeli:** < 500ms dla 5k rekordów
- **Edycja pola:** < 50ms (bez requestów)
- **Eksport:** < 1s dla 10k rekordów

### **Optymalizacje:**
- **Virtual Scrolling** dla >1k rekordów
- **Debounced Updates** przy szybkiej edycji
- **Lazy Validation** - tylko widoczne pola
- **Memory Management** - cleanup niepotrzebnych danych

---

## 🧪 **STRATEGIA TESTOWANIA**

### **Test Cases:**
1. **Parsing Accuracy:** Porównanie wyników starej i nowej architektury
2. **Edit Performance:** Czas reakcji na edycje inline vs modal
3. **Data Integrity:** Sprawdzenie czy wszystkie dane są zachowane
4. **Export Consistency:** Porównanie TSV output
5. **Memory Usage:** Zużycie pamięci przy dużych zbiorach
6. **Offline Capability:** Funkcjonalność bez backendu

### **Test Data:**
- Mały zbiór: 100 rekordów (wszystkie typy)
- Średni zbiór: 1k rekordów
- Duży zbiór: 10k rekordów
- Edge cases: puste pola, błędne dane, specjalne znaki

---

## 🚀 **ROADMAP PO MIGRACJI**

### **Faza 2.1 - Core UX Enhancements (Natychmiast po migracji):**
- **Persistencia sesji:** Auto-zapisywanie appState do localStorage co 30s, odzyskiwanie przy starcie
- **Tryb porównania:** Zachowaj originalRecords[], pokaż zmiany z podświetleniami
- **Global undo:** Stack ostatnich 20-50 akcji z przyciskiem cofnij
- Undo/Redo functionality
- Bulk edit operations
- Advanced filtering and search

### **Faza 2.2 - Data Management & Analytics:**
- **Statystyki kontekstowe:** Liczniki błędów, rozkład wieków, najczęstsze nazwiska
- **System tagów:** Ręczne tagowanie rekordów z filtrami i kolorowymi paskami
- **Konfigurowalny widok:** Wybór kolumn, drag&drop kolejności, zapis preferencji
- Context-aware validation (wiek vs epoka)
- Fuzzy matching for names
- Historical name variants

### **Faza 2.3 - Advanced Features:**
- **Tryb karta na mobile:** Automatyczne przełączanie na <768px z kartami
- **Zaawansowany eksport:** Checkboxy dla formatów, tylko zmodyfikowane, metadane
- **Podgląd pliku:** Mini-preview przed wczytaniem z wyborem delimitera
- **Bulk tagging:** "Oznacz wszystkie czerwone jako do sprawdzenia"
- Multi-user editing
- Change tracking and comments

### **Faza 2.4 - Analytics & Integration:**
- Statistical analysis
- Data quality reports
- Trend analysis
- Genealogical insights
- Data sharing and export
- Integration with external databases