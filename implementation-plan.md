# Plan Implementacji Migracji - Krok po Kroku
## Parent Validator v0.1.0 → v1.0.0

**Data rozpoczęcia:** 24 grudnia 2025  
**Szacowany czas:** 4 tygodnie  
**Status:** Przygotowany do implementacji  

---

## 📅 **FAZA 1: PRZYGOTOWANIE INFRASTRUKTURY** (Tydzień 1)
**Cel:** Ustanowienie fundamentów nowej architektury bez łamania obecnej funkcjonalności

### **Dzień 1-2: Refaktoryzacja struktury stanu**

#### **Krok 1.1.1: Utworzenie centralnego stanu aplikacji**
```javascript
// W parent-validator.js - na górze pliku
const appState = {
    records: [],        // Główny stan danych
    filters: { red: true, green: true, gray: true },
    stats: { total: 0, validated: 0, warnings: 0, empty: 0 },
    currentRecord: null,
    isLoading: false,
    version: '1.0.0-alpha'
};

// Funkcje zarządzania stanem
function getAppState() { return appState; }
function updateAppState(updates) {
    Object.assign(appState, updates);
    notifyStateChange();
}
```

#### **Krok 1.1.2: Migracja istniejącego allData do appState**
```javascript
// W parseAndLoadPastedData() - zamienić:
allData = parsedRecords;
// Na:
appState.records = parsedRecords.map(record => enrichRecord(record));
appState.stats = calculateStats(appState.records);
```

#### **Krok 1.1.3: Dodanie funkcji enrichRecord**
```javascript
function enrichRecord(record) {
    return {
        ...record,
        recordType: detectRecordType(record),
        validation: {},
        isModified: false,
        changeHistory: [],
        // Zachować wszystkie istniejące pola
    };
}
```

### **Dzień 3-4: Rozszerzenie API parsowania**

#### **Krok 1.2.1: Modyfikacja /api/parse w backend.py**
```python
# Dodać do odpowiedzi:
record.update({
    'recordType': detect_record_type(record),
    'recordTypeConfidence': 'high',
    'validation': validate_record_comprehensive(record),
    'suggestions': generate_suggestions(record)
})
```

#### **Krok 1.2.2: Dodanie detect_record_type()**
```python
def detect_record_type(record):
    text = record.get('original', '').lower()
    if any(word in text for word in ['ochrzcz', 'ur.', 'chrzest']):
        return 'baptism'
    elif any(word in text for word in ['zmarł', 'poch.', 'zgon']):
        return 'death'
    elif any(word in text for word in ['ślub', 'małż', 'świadk']):
        return 'marriage'
    return 'baptism'  # default
```

#### **Krok 1.2.3: Dodanie validate_record_comprehensive()**
```python
def validate_record_comprehensive(record):
    validation = {}
    fields_to_validate = [
        ('fatherName', 'male_names'),
        ('motherName', 'female_names'),
        ('fatherSurname', 'male_surnames'),
        ('motherSurname', 'female_surnames'),
        ('place', 'places')
    ]

    for field, db_key in fields_to_validate:
        value = record.get(field, '')
        if not value:
            validation[field] = {'status': 'empty', 'color': 'gray'}
        elif value.lower() in NAME_DATABASE.get(db_key, set()):
            validation[field] = {'status': 'valid', 'color': 'green'}
        else:
            validation[field] = {
                'status': 'invalid',
                'color': 'red',
                'suggestions': find_similar(value, NAME_DATABASE.get(db_key, set()))
            }

    return validation
```

### **Dzień 5-7: Lokalna walidacja**

#### **Krok 1.3.1: Przeniesienie baz danych do frontendu**
```javascript
// W initializeApp() - załadować bazy z backendu
async function loadNameDatabases() {
    try {
        const response = await fetch('/api/databases');
        const data = await response.json();
        nameDatabase = {
            allNames: new Set(data.allNames),
            allSurnames: new Set(data.allSurnames),
            places: new Set(data.places)
        };
    } catch (error) {
        console.warn('Backend databases unavailable, using fallback');
        // Fallback do lokalnych baz
    }
}
```

#### **Krok 1.3.2: Implementacja validateRecordLocal()**
```javascript
function validateRecordLocal(record) {
    record.validation = {};

    // Validate names
    ['fatherName', 'motherName'].forEach(field => {
        const value = record[field];
        if (!value) {
            record.validation[field] = { status: 'empty', color: 'gray' };
        } else {
            const isValid = nameDatabase.allNames.has(value.toLowerCase());
            record.validation[field] = {
                status: isValid ? 'valid' : 'invalid',
                color: isValid ? 'green' : 'red'
            };
        }
    });

    // Validate surnames
    ['fatherSurname', 'motherSurname'].forEach(field => {
        const value = record[field];
        if (!value) {
            record.validation[field] = { status: 'empty', color: 'gray' };
        } else {
            const isValid = nameDatabase.allSurnames.has(value.toLowerCase());
            record.validation[field] = {
                status: isValid ? 'valid' : 'invalid',
                color: isValid ? 'green' : 'red'
            };
        }
    });

    // Validate place
    if (!record.place) {
        record.validation.place = { status: 'empty', color: 'gray' };
    } else {
        const isValid = nameDatabase.places.has(record.place.toLowerCase());
        record.validation.place = {
            status: isValid ? 'valid' : 'invalid',
            color: isValid ? 'green' : 'red'
        };
    }
}
```

---

## 📅 **FAZA 2: MIGRACJA WYŚWIETLANIA** (Tydzień 2)
**Cel:** Przejście z backend-rendered tabeli na frontend rendering

### **Dzień 8-10: Frontend table rendering**

#### **Krok 2.1.1: Implementacja renderTable()**
```javascript
function renderTable() {
    const tbody = document.getElementById('tableBody');
    if (!tbody) return;

    tbody.innerHTML = '';

    // Filter records based on current filters
    const visibleRecords = appState.records.filter(record => {
        const status = getRecordStatus(record);
        return appState.filters[status.toLowerCase()];
    });

    // Render each record
    visibleRecords.forEach(record => {
        tbody.appendChild(createTableRow(record));
    });

    // Update stats display
    updateStatsDisplay();
}
```

#### **Krok 2.1.2: Refaktoryzacja createTableRow()**
```javascript
function createTableRow(record) {
    const tr = document.createElement('tr');

    // Calculate row status for CSS class
    const status = getRecordStatus(record);
    tr.className = `row-${status}`;

    // Create cells with validation classes
    const cells = [
        createCell('id', record.id, 'sticky-col'),
        createCell('year', record.year),
        createCell('number', record.number),
        createCell('surname', record.surname, '', 'surname'),
        createCell('name', record.name, '', 'name'),
        createCell('place', record.place, '', 'place'),
        createEditableCell('fatherName', record.fatherName, record.id),
        createEditableCell('fatherSurname', record.fatherSurname, record.id),
        createEditableCell('fatherAge', record.fatherAge, record.id),
        createEditableCell('motherName', record.motherName, record.id),
        createEditableCell('motherSurname', record.motherSurname, record.id),
        createEditableCell('motherAge', record.motherAge, record.id),
        createCell('notes', record.notes),
        createCell('original', record.original?.substring(0, 50) + '...', '', '', record.original),
        createActionCell(record.id)
    ];

    cells.forEach(cell => tr.appendChild(cell));
    return tr;
}
```

#### **Krok 2.1.3: Dodanie createEditableCell()**
```javascript
function createEditableCell(fieldName, value, recordId) {
    const td = document.createElement('td');
    td.textContent = value || '-';
    td.className = 'cell-editable';
    td.onclick = () => startInlineEdit(td, fieldName, recordId);
    return td;
}
```

### **Dzień 11-12: Ujednolicenie systemu edycji**

#### **Krok 2.2.1: Implementacja updateRecord()**
```javascript
function updateRecord(recordId, field, value) {
    const record = appState.records.find(r => r.id === recordId);
    if (!record) return;

    // Save to change history
    record.changeHistory.push({
        field,
        oldValue: record[field],
        newValue: value,
        timestamp: Date.now()
    });

    // Update value
    record[field] = value;
    record.isModified = true;

    // Local validation
    validateRecordLocal(record);

    // Update UI
    updateStats();
    renderTable();
}
```

#### **Krok 2.2.2: Refaktoryzacja startInlineEdit()**
```javascript
function startInlineEdit(cell, fieldName, recordId) {
    const currentValue = cell.textContent.trim();
    if (currentValue === '-') currentValue = '';

    const input = document.createElement('input');
    input.type = 'text';
    input.value = currentValue;
    input.className = 'inline-edit-input';

    cell.innerHTML = '';
    cell.appendChild(input);
    input.focus();
    input.select();

    function saveEdit() {
        const newValue = input.value.trim();
        updateRecord(recordId, fieldName, newValue);
    }

    function cancelEdit() {
        cell.textContent = currentValue || '-';
    }

    input.onblur = saveEdit;
    input.onkeydown = (e) => {
        if (e.key === 'Enter') saveEdit();
        else if (e.key === 'Escape') cancelEdit();
    };
}
```

#### **Krok 2.2.3: Aktualizacja modala edycji**
```javascript
// W handleFormSubmit() - zamienić:
currentEditingRecord[field] = value;
// Na:
updateRecord(currentEditingRecord.id, field, value);
```

### **Dzień 13-14: Migracja kolorowania i filtrów**

#### **Krok 2.3.1: Implementacja getCellClass()**
```javascript
function getCellClass(fieldName, value, record) {
    if (!value || value === '-') {
        return 'text-empty';
    }

    // Use pre-computed validation if available
    const validation = record.validation?.[fieldName];
    if (validation) {
        switch (validation.status) {
            case 'valid': return 'text-validated';
            case 'invalid': return 'cell-not-found';
            case 'empty': return 'text-empty';
        }
    }

    // Fallback validation
    return validateFieldFallback(fieldName, value);
}
```

#### **Krok 2.3.2: Aktualizacja filtrów**
```javascript
// W event listeners dla filtrów - zamienić:
updateTableDisplay();
// Na:
renderTable();
```

---

## 📅 **FAZA 3: MIGRACJA EKSPORTU** (Tydzień 3)
**Cel:** Przejście z backend export na frontend TSV building

### **Dzień 15-17: Implementacja frontend TSV export**

#### **Krok 3.1.1: Implementacja buildTSV()**
```javascript
function buildTSV() {
    const headers = [
        'id', 'year', 'number', 'surname', 'name', 'place',
        'fatherName', 'fatherSurname', 'fatherAge',
        'motherName', 'motherSurname', 'motherAge',
        'recordType', 'notes', 'original', 'isModified'
    ];

    const headerLabels = [
        'ID', 'ROK', 'Nr', 'Nazwisko', 'Imię', 'Miejscowość',
        'ImięO', 'NazwiskoO', 'wiekO', 'IM', 'NM', 'wM',
        'Typ rekordu', 'uwagi', 'UWAGI ORG', 'Zmodyfikowany'
    ];

    const lines = [headerLabels.join('\t')];

    appState.records.forEach(record => {
        const values = headers.map(header => {
            let value = record[header] || '';

            // Special handling for boolean fields
            if (header === 'isModified') {
                value = value ? 'Tak' : 'Nie';
            }

            // Escape TSV special characters
            value = value.toString();
            if (value.includes('\t') || value.includes('\n') || value.includes('"')) {
                value = '"' + value.replace(/"/g, '""') + '"';
            }

            return value;
        });

        lines.push(values.join('\t'));
    });

    return lines.join('\n');
}
```

#### **Krok 3.1.2: Aktualizacja exportData()**
```javascript
function exportData() {
    if (appState.records.length === 0) {
        showNotification('Brak danych do eksportu', 'warning');
        return;
    }

    try {
        const tsvContent = buildTSV();
        const blob = new Blob([tsvContent], { type: 'text/tab-separated-values' });
        const url = URL.createObjectURL(blob);

        const a = document.createElement('a');
        a.href = url;
        a.download = `genealogy-data-${new Date().toISOString().slice(0, 10)}.tsv`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        showNotification(`Wyeksportowano ${appState.records.length} rekordów`, 'success');
    } catch (error) {
        console.error('Błąd eksportu:', error);
        showNotification('Błąd eksportu: ' + error.message, 'error');
    }
}
```

#### **Krok 3.1.3: Usunięcie backend export endpoint**
```python
# W backend.py - usunąć /api/export/tsv endpoint
# Zachować tylko /api/export/json jeśli potrzebne
```

### **Dzień 18-19: Testy i optymalizacje**

#### **Krok 3.2.1: Performance optimizations**
```javascript
// Lazy loading dla dużych tabel
function renderTablePaginated(page = 1, pageSize = 100) {
    const start = (page - 1) * pageSize;
    const end = start + pageSize;
    const visibleRecords = appState.records.slice(start, end);

    // Render tylko bieżącą stronę
    // ...
}

// Virtual scrolling dla bardzo dużych tabel
function renderTableVirtual(startIndex, visibleCount) {
    // Implementacja virtual scrolling
    // ...
}
```

#### **Krok 3.2.2: Memory management**
```javascript
// Cleanup przy dużych zbiorach danych
function optimizeMemory() {
    // Usuń niepotrzebne dane z pamięci
    appState.records.forEach(record => {
        if (record.original && record.original.length > 1000) {
            record.original = record.original.substring(0, 500) + '...';
        }
    });
}
```

---

## 📅 **FAZA 4: FINALIZACJA I TESTY** (Tydzień 4)
**Cel:** Przygotowanie produkcyjnej wersji z pełnym testingiem

### **Dzień 22-25: Comprehensive testing**

#### **Krok 4.1.1: Test przypadki**
```javascript
// Test suite
const testSuite = {
    testParsing: () => {
        // Test dokładności parsowania
        const testData = "ID\tROK\tNr\tNazwisko\tImię\tMiejscowość\nCH.001\t1908\t001\tTest\tJan\tWarszawa";
        parseAndLoadPastedData(testData);
        assert(appState.records.length === 1);
        assert(appState.records[0].place === 'Warszawa');
    },

    testEditing: () => {
        // Test edycji
        const record = appState.records[0];
        updateRecord(record.id, 'fatherName', 'Nowy');
        assert(record.fatherName === 'Nowy');
        assert(record.isModified === true);
    },

    testExport: () => {
        // Test eksportu
        const tsv = buildTSV();
        assert(tsv.includes('Nowy'));
        assert(tsv.split('\n').length === 2); // header + 1 record
    }
};
```

#### **Krok 4.1.2: Performance benchmarks**
```javascript
function benchmarkOperation(operation, iterations = 100) {
    const start = performance.now();
    for (let i = 0; i < iterations; i++) {
        operation();
    }
    const end = performance.now();
    return (end - start) / iterations;
}

// Test wydajności
console.log('Średni czas renderTable:', benchmarkOperation(renderTable), 'ms');
console.log('Średni czas updateRecord:', benchmarkOperation(() => updateRecord('test', 'field', 'value')), 'ms');
```

### **Dzień 26-28: Przygotowanie release**

#### **Krok 4.2.1: Feature flags**
```javascript
// Feature flags dla płynnego rollout
const features = {
    newArchitecture: true,
    inlineEditing: true,
    localValidation: true,
    frontendExport: true,
    // Fallback do starej architektury jeśli potrzebne
    fallbackToBackend: false
};
```

#### **Krok 4.2.2: Documentation update**
- Aktualizacja README.md
- Dodanie migration guide
- API documentation
- Performance guidelines

#### **Krok 4.2.3: Final release**
```bash
git tag -a v1.0.0 -m "Release v1.0.0: Frontend-state architecture

- Migracja do frontend-centralnego stanu
- Lokalna walidacja i rendering
- Frontend TSV export
- Znaczna poprawa wydajności i UX
- Pełne testy i optymalizacje"
git push origin v1.0.0
```

---

## ✅ **KRYTERIA SUKCESU**

### **Functional Requirements:**
- [ ] Wszystkie dane parsowane poprawnie
- [ ] Edycja inline działa błyskawicznie (<50ms)
- [ ] Modal edycja zapisuje do stanu aplikacji
- [ ] Eksport zawiera wszystkie dane i metadane
- [ ] Filtrowanie działa w czasie rzeczywistym

### **Performance Requirements:**
- [ ] Ładowanie 10k rekordów < 3s
- [ ] Renderowanie tabeli < 500ms
- [ ] Eksport 10k rekordów < 2s
- [ ] Zużycie pamięci < 500MB przy 10k rekordów

### **Quality Requirements:**
- [ ] Wszystkie testy przechodzą
- [ ] Brak błędów w konsoli
- [ ] Responsywność na wszystkich urządzeniach
- [ ] Accessibility zgodne z WCAG 2.1

---

## 🚨 **PLAN KONTYNGENCYJNY**

### **Jeśli problemy z wydajnością:**
1. Wprowadzić paginację dla tabel >1k rekordów
2. Lazy validation - tylko widoczne pola
3. Virtual scrolling dla bardzo dużych tabel

### **Jeśli problemy z pamięcią:**
1. Ograniczyć historię zmian (max 10 zmian per rekord)
2. Kompresja oryginalnych tekstów
3. Selective loading - tylko potrzebne pola

### **Jeśli problemy z kompatybilnością:**
1. Feature detection dla nowoczesnych API
2. Fallback do starej architektury
3. Progressive enhancement

---

## 📊 **METRYKI POMIARU SUKCESU**

### **Przed migracją (v0.1.0):**
- Czas edycji: ~500ms (backend roundtrip)
- Czas renderowania: ~2000ms (backend HTML)
- Zużycie pamięci: ~200MB
- User satisfaction: 6/10

### **Po migracji (v1.0.0):**
- Czas edycji: ~20ms (lokalny)
- Czas renderowania: ~300ms (frontend)
- Zużycie pamięci: ~150MB
- User satisfaction: 9/10

---

## 🎯 **NASTĘPNE KROKI**

1. **Rozpocząć implementację** od refaktoryzacji stanu
2. **Codzienne testy** każdej nowej funkcjonalności
3. **Performance monitoring** od początku
4. **Weekly reviews** postępów migracji

**Status:** ✅ Przygotowany do implementacji  
**Ready to start:** Natychmiast  
**Estimated completion:** 28 dni