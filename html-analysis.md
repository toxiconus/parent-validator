# 🔍 Analiza HTML - Parent Validator (POPRAWIONA)

**Data analizy**: 21 grudnia 2025  
**Cel**: Uniwersalność, bezpieczeństwo danych, poprawna logika nazwisk

---

## ⚠️ BŁĘDNE ZAŁOŻENIA (poprzednia analiza)

❌ **"Tabela 14 kolumn to za dużo"** → ŹLE! Liczba kolumn = liczba w źródle  
❌ **"Usuń kolumnę ORG"** → NIEBEZPIECZNE! Nigdy nie usuwać oryginalnych danych  
❌ **"Automatycznie kopiuj nazwisko dziecka do matki"** → ŹLE! Panieńskie ≠ nazwisko dziecka

---

## ✅ PRAWDZIWE WYMAGANIA

### 1. **DYNAMICZNA LICZBA KOLUMN**

**Fakty:**
- ✅ Liczba kolumn = liczba w pliku źródłowym
- ✅ Może być **5, 15, 30, 50+** kolumn
- ✅ Różne typy aktów mają różne struktury:
  - Chrzty: ~12-15 kolumn (ID, imię dziecka, nazwisko, rok, miejsce, rodzice...)
  - Małżeństwa: ~20 kolumn (para młoda, rodzice obojga, świadkowie...)
  - Zgony: ~15-20 kolumn (zmarły, przyczyna, rodzina, świadkowie...)

**Co jest potrzebne:**
1. **Automatyczne rozpoznawanie kolumn według treści**
   - ID aktu (regex: `^[A-Z]{2,}\.[A-Z]{3,}\.\d+`)
   - Daty (regex: `\d{4}` lub `\d{2}\.\d{2}`)
   - Imiona (sprawdź w `imiona_wszystkie.json`)
   - Nazwiska (sprawdź w `nazwiska_wszystkie.json`)

2. **Mapowanie kolumn** (jak w `/paste/mapper.js`)
   - Drag & drop źródło → cel
   - Zapisywanie konfiguracji w localStorage
   - Auto-sugestie na podstawie treści

3. **Scroll poziomy = OK!**
   - Szeroka tabela to nie bug, to cecha
   - Użytkownik może przewijać w prawo

---

### 2. **KOLUMNA ORG JEST KRYTYCZNA**

**NIGDY NIE USUWAJ!** To jedyne źródło prawdy.

**Wymagania:**
✅ Musi zawierać **pełną oryginalną linię**  
✅ Separatory: `\t` (TAB) → `|` (pionowa kreska) dla czytelności  
✅ Kliknięcie → modal z oryginalną linią  
✅ Przycisk "📋 Kopiuj oryginał"

**Przykład:**
```
Źródło (TSV z TAB):
CH.LUB.001	Kowalski	Jan	1	1850	12.05.1850	Warszawa	Piotr	Kowalska	Anna	Nowak

Kolumna ORG pokazuje:
CH.LUB.001|Kowalski|Jan|1|1850|12.05.1850|Warszawa|Piotr|Kowalska|Anna|Nowak
         ↑ TAB zamieniony na | dla czytelności
```

**Implementacja - Modal z oryginalną linią:**
```html
<div class="modal-overlay" id="originalModal">
    <div class="modal-content">
        <div class="modal-header">
            <h2>📄 Oryginalna linia danych</h2>
            <button class="close-btn" onclick="closeOriginalModal()">×</button>
        </div>
        <div class="modal-body">
            <pre id="originalText" class="original-line-display">
CH.LUB.001 | Kowalski | Jan | 1 | 1850 | 12.05.1850 | Warszawa | Piotr | Kowalska | Anna | Nowak
            </pre>
            <button class="btn btn-primary" onclick="copyOriginalToClipboard()">
                <span class="material-icons">content_copy</span> Kopiuj do schowka
            </button>
        </div>
    </div>
</div>
```

**CSS:**
```css
.original-line-display {
    background: #1e1e1e;
    color: #d4d4d4;
    padding: 1rem;
    border-radius: 6px;
    overflow-x: auto;
    font-family: 'Courier New', monospace;
    font-size: 0.9rem;
    line-height: 1.6;
    white-space: pre-wrap;
    word-break: break-all;
}

.col-original {
    cursor: pointer;
    color: #667eea;
    font-weight: 600;
}

.col-original:hover {
    text-decoration: underline;
}
```

---

### 3. **ZŁOŻONA LOGIKA NAZWISK** (NAJWAŻNIEJSZE!)

#### 📌 REGUŁA 1: Nazwisko matki

❌ **BŁĄD**: Automatyczne kopiowanie nazwiska dziecka do matki  
✅ **POPRAWNE**: Panieńskie matki ≠ nazwisko dziecka

**Przypadki:**

**A) Nazwisko panieńskie = nazwisko dziecka**
```
Dziecko: Maria Kowalska
Ojciec: Jan Nowak
Matka: Anna Kowalska (panieńskie)

Interpretacja:
- Możliwy **zbieg okoliczności** (matka z rodziny Kowalskich)
- LUB dziecko **nieślubne** (nosi nazwisko matki)
- LUB matka z **tej samej rodziny co ojciec** (kuzynostwo)

→ NIE zmieniaj automatycznie! Oznacz jako "⚠️ Sprawdź kontekst"
```

**B) Brak nazwiska panieńskiego**
```
Dziecko: Józef Kowalski
Ojciec: Piotr Kowalski
Matka: Anna (brak nazwiska)

→ Pozostaw puste, CZEKAJ na uzupełnienie przez użytkownika
```

#### 📌 REGUŁA 2: Nazwisko ojca

✅ **Jeśli ojciec ma imię BEZ nazwiska** → nazwisko = nazwisko dziecka

**Przypadek:**
```
Dziecko: Jan Kowalski
Ojciec: Piotr (bez nazwiska)
Matka: Anna Nowak (panieńskie)

Logika:
Dziecko zwykle dziedziczy nazwisko ojca
→ Jeśli dziecko = Kowalski, to ojciec = Kowalski

Uzupełnij:
Ojciec: Piotr Kowalski ✅
```

#### 📌 REGUŁA 3: Brak danych (kontekst!)

**Oznaczenia:**
- `"x"` = brak danych / nieznany
- `".."` = brak danych / puste
- `"?"` = niepewny / nieczytelny

**Przypadki:**

**A) Ojciec nieznany**
```
Dziecko: Anna Nowak
Ojciec: x
Matka: Marianna Nowak (panieńskie)

→ Ojciec nieznany (dziecko nieślubne?)
→ Nazwisko dziecka = nazwisko matki
```

**B) Kontekst historyczny**
```
"Piotr .. Kowalski"
        ↑ Brak drugiego imienia lub patronimu

"Jan i .. Nowak"
       ↑ Brak imienia matki (nieczytelny zapis)
```

---

## ❌ RZECZYWISTE PROBLEMY UI

### Problem 1: BRAK MAPOWANIA KOLUMN

**Obecny stan:**
- ❌ System zakłada **sztywne 14 kolumn**
- ❌ Nie rozpoznaje kolumn automatycznie
- ❌ Co jeśli źródło ma inną kolejność?

**Rozwiązanie:**
Zaimplementuj system mapowania jak w `/paste/mapper.js`:

```javascript
// 1. Auto-detekcja typu kolumny
function detectColumnType(headerName, sampleValues) {
    const header = headerName.toLowerCase();
    
    // ID aktu
    if (/id|identyfikator|numer/.test(header)) {
        return 'id';
    }
    
    // Rok
    if (/rok|year/.test(header) || sampleValues.every(v => /^\d{4}$/.test(v))) {
        return 'year';
    }
    
    // Imię - sprawdź w bazie
    if (/imię|first|name/.test(header)) {
        const inDatabase = sampleValues.some(v => 
            nameDatabase.allNames.has(v.toLowerCase())
        );
        return inDatabase ? 'firstName' : 'unknown';
    }
    
    // ... więcej reguł
}

// 2. Modal mapowania kolumn
function showColumnMappingModal(detectedColumns) {
    const modal = `
        <div class="mapping-modal">
            <h2>📋 Mapowanie kolumn</h2>
            <p>Przeciągnij kolumny źródłowe do pól docelowych:</p>
            
            <div class="mapping-grid">
                <div class="source-columns">
                    ${detectedColumns.map(col => `
                        <div class="source-col" draggable="true" data-index="${col.index}">
                            <strong>${col.header}</strong><br>
                            <small>Przykład: ${col.sample}</small><br>
                            <span class="detected-type">${col.detectedType}</span>
                        </div>
                    `).join('')}
                </div>
                
                <div class="target-slots">
                    <div class="target-slot" data-field="id">ID aktu</div>
                    <div class="target-slot" data-field="surname">Nazwisko dziecka</div>
                    <div class="target-slot" data-field="firstName">Imię dziecka</div>
                    <div class="target-slot" data-field="year">Rok</div>
                    <div class="target-slot" data-field="place">Miejsce</div>
                    <div class="target-slot" data-field="fatherName">Imię ojca</div>
                    <div class="target-slot" data-field="fatherSurname">Nazwisko ojca</div>
                    <div class="target-slot" data-field="motherName">Imię matki</div>
                    <div class="target-slot" data-field="motherSurname">Nazwisko matki (panieńskie!)</div>
                    <div class="target-slot" data-field="notes">Uwagi</div>
                    <div class="target-slot" data-field="original">ORG (pełna linia)</div>
                </div>
            </div>
            
            <button onclick="saveMapping()">✅ Zapisz mapowanie</button>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', modal);
}
```

**Zapisywanie konfiguracji:**
```javascript
// localStorage dla powtarzalności
const mappingConfig = {
    sourceFormat: 'chrzty_lublin_blinow',
    timestamp: new Date().toISOString(),
    mapping: {
        0: 'id',
        1: 'surname',
        2: 'firstName',
        // ...
    }
};

localStorage.setItem('agene_column_mapping', JSON.stringify(mappingConfig));
```

---

### Problem 2: BRAK ONBOARDINGU

**Obecny stan:**
- ❌ 4 przyciski załadowania + textarea + 3 przyciski akcji = **7 opcji**
- ❌ Użytkownik nie wie **od czego zacząć**
- ❌ Brak wyjaśnienia **"po co to w ogóle?"**

**Rozwiązanie:**
Modal przy pierwszym uruchomieniu:

```html
<div class="first-time-overlay" id="firstTimeOverlay">
    <div class="onboarding-card">
        <h2>👋 Witaj w Edytorze Rodziców!</h2>
        
        <div class="what-it-does">
            <p><strong>Co to robi?</strong></p>
            <p>Przekształca połączone dane rodziców w osobne pola + waliduje je w bazie polskich imion</p>
        </div>
        
        <div class="example-transform">
            <div class="before-example">
                ❌ <code>"Wawrzeniec i Katarzyna Woytowicz"</code>
            </div>
            <div class="arrow">↓</div>
            <div class="after-example">
                ✅ Ojciec: <input disabled value="Wawrzeniec"> <input disabled value="Woytowicz"><br>
                ✅ Matka: <input disabled value="Katarzyna"> <input disabled value="?"> 
                <span class="warning-badge">⚠️ Brak panieńskiego</span>
            </div>
        </div>
        
        <div class="choose-method">
            <p><strong>Wybierz sposób załadowania:</strong></p>
            
            <button class="method-btn recommended" onclick="chooseMethod('excel')">
                <div class="method-icon">📊</div>
                <div class="method-details">
                    <strong>Wklej z Excela</strong>
                    <small>Najczęstsze - Ctrl+C w Excel → Ctrl+V tutaj</small>
                </div>
                <span class="recommended-badge">Polecane</span>
            </button>
            
            <button class="method-btn" onclick="chooseMethod('file')">
                <div class="method-icon">📁</div>
                <div class="method-details">
                    <strong>Załaduj plik</strong>
                    <small>TSV, CSV, TXT - prześlij z dysku</small>
                </div>
            </button>
            
            <button class="method-btn" onclick="chooseMethod('parser')">
                <div class="method-icon">⚙️</div>
                <div class="method-details">
                    <strong>Dane z parsera</strong>
                    <small>5947 rekordów z akt chrztów (gotowe do edycji)</small>
                </div>
            </button>
            
            <button class="method-btn" onclick="chooseMethod('example')">
                <div class="method-icon">📝</div>
                <div class="method-details">
                    <strong>Przykładowe dane</strong>
                    <small>3 rekordy testowe - zobacz jak to działa</small>
                </div>
            </button>
        </div>
        
        <label class="dont-show-again">
            <input type="checkbox" id="dontShowAgain">
            Nie pokazuj tego więcej
        </label>
    </div>
</div>
```

**CSS:**
```css
.first-time-overlay {
    position: fixed;
    top: 0; left: 0;
    width: 100vw; height: 100vh;
    background: rgba(0,0,0,0.85);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 10000;
    animation: fadeIn 0.3s ease;
}

.onboarding-card {
    background: white;
    border-radius: 16px;
    padding: 2.5rem;
    max-width: 700px;
    max-height: 90vh;
    overflow-y: auto;
    box-shadow: 0 20px 60px rgba(0,0,0,0.5);
}

.what-it-does {
    background: #f8f9ff;
    padding: 1rem;
    border-radius: 8px;
    border-left: 4px solid #667eea;
    margin: 1rem 0;
}

.example-transform {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    margin: 1.5rem 0;
    padding: 1rem;
    background: #f8f9fa;
    border-radius: 8px;
}

.before-example {
    color: #dc3545;
    font-size: 1.1rem;
}

.after-example {
    color: #28a745;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
}

.arrow {
    text-align: center;
    font-size: 2rem;
    color: #667eea;
}

.method-btn {
    display: flex;
    align-items: center;
    gap: 1rem;
    width: 100%;
    padding: 1rem;
    margin: 0.5rem 0;
    border: 2px solid #e9ecef;
    border-radius: 10px;
    background: white;
    cursor: pointer;
    transition: all 0.2s;
    position: relative;
}

.method-btn:hover {
    border-color: #667eea;
    background: #f8f9ff;
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.15);
}

.method-btn.recommended {
    border-color: #28a745;
    background: #f0fff4;
}

.recommended-badge {
    position: absolute;
    top: -8px;
    right: 10px;
    background: #28a745;
    color: white;
    font-size: 0.7rem;
    padding: 2px 8px;
    border-radius: 10px;
    font-weight: 600;
}

.method-icon {
    font-size: 2rem;
}

.method-details {
    flex: 1;
    text-align: left;
}

.method-details strong {
    display: block;
    margin-bottom: 0.25rem;
}

.method-details small {
    color: #6c757d;
    font-size: 0.85rem;
}
```

**JavaScript:**
```javascript
// Sprawdź przy starcie
document.addEventListener('DOMContentLoaded', function() {
    const firstTime = localStorage.getItem('agene_first_time');
    
    if (!firstTime) {
        // Pokaż onboarding
        document.getElementById('firstTimeOverlay').style.display = 'flex';
    }
    
    // Obsługa "Nie pokazuj więcej"
    document.getElementById('dontShowAgain').addEventListener('change', function(e) {
        if (e.target.checked) {
            localStorage.setItem('agene_first_time', 'completed');
        }
    });
});

function chooseMethod(method) {
    // Zamknij modal
    document.getElementById('firstTimeOverlay').style.display = 'none';
    
    // Zaznacz "nie pokazuj więcej"
    localStorage.setItem('agene_first_time', 'completed');
    
    // Wykonaj akcję
    switch(method) {
        case 'excel':
            document.getElementById('pasteTextarea').focus();
            showNotification('Wklej dane z Excela (Ctrl+V)', 'info');
            break;
        case 'file':
            document.getElementById('fileInput').click();
            break;
        case 'parser':
            loadParserResults();
            break;
        case 'example':
            loadExampleData();
            break;
    }
}
```

---

### Problem 3: TOGGLE "OPCJE" MYLĄCY

**Obecny stan:**
```html
<button class="btn-toggle-controls">
    <span class="material-icons">expand_more</span> Opcje
</button>
```

Problemy:
- ❌ Ikona statyczna (`expand_more`) - nie zmienia się
- ❌ Tekst "Opcje" niejasny - opcje czego?
- ❌ Nie widać czy rozwinięte czy zwinięte

**Rozwiązanie:**
```html
<button class="btn-toggle-controls" onclick="toggleTableControls()">
    <span class="material-icons" id="toggleIcon">expand_more</span> 
    <span id="toggleText">Pokaż filtry i akcje</span>
</button>
```

**JavaScript:**
```javascript
function toggleTableControls() {
    tableControlsExpanded = !tableControlsExpanded;
    
    const filterGroup = document.getElementById('filterGroup');
    const actionGroup = document.getElementById('actionGroup');
    const toggleBtn = document.querySelector('.btn-toggle-controls');
    const icon = document.getElementById('toggleIcon');
    const text = document.getElementById('toggleText');
    
    if (tableControlsExpanded) {
        filterGroup.style.display = 'grid';
        actionGroup.style.display = 'flex';
        toggleBtn.classList.add('expanded');
        icon.textContent = 'expand_less';  // ↑ Ikona zmienia się!
        text.textContent = 'Ukryj filtry i akcje';
    } else {
        filterGroup.style.display = 'none';
        actionGroup.style.display = 'none';
        toggleBtn.classList.remove('expanded');
        icon.textContent = 'expand_more';  // ↓ Wraca do domyślnej
        text.textContent = 'Pokaż filtry i akcje';
    }
}
```

**CSS - wizualne oznaczenie stanu:**
```css
.btn-toggle-controls {
    transition: all 0.3s ease;
}

.btn-toggle-controls.expanded {
    background: #667eea;
    color: white;
}

.btn-toggle-controls.expanded:hover {
    background: #5a6fd8;
}
```

---

### Problem 4: POPRAWNA LOGIKA NAZWISK

**Zaimplementuj 3 reguły:**

```javascript
/**
 * Inteligentne uzupełnianie nazwisk - POPRAWNA LOGIKA
 */
function inferParentSurnames(record) {
    const warnings = [];
    
    // ========================================
    // REGUŁA 1: Nazwisko ojca
    // ========================================
    if (record.fatherName && 
        !record.fatherSurname && 
        record.fatherName !== 'x' && 
        record.fatherName !== '..' &&
        record.fatherName !== '?') {
        
        // Jeśli ojciec ma imię bez nazwiska → nazwisko dziecka
        record.fatherSurname = record.surname;
        record.fatherSurnameSource = 'inferred_from_child';
        
        console.log(`✓ Uzupełniono nazwisko ojca: ${record.fatherSurname} (z dziecka)`);
    }
    
    // ========================================
    // REGUŁA 2: Nazwisko matki - NIE KOPIUJ!
    // ========================================
    // Panieńskie matki ≠ nazwisko dziecka (zazwyczaj)
    
    if (record.motherSurname === record.surname) {
        // To może być:
        // 1) Zbieg okoliczności (matka z rodziny Kowalskich, dziecko też Kowalski)
        // 2) Dziecko nieślubne (nosi nazwisko matki)
        // 3) Małżeństwo kuzynów (oboje Kowalscy)
        
        warnings.push({
            type: 'surname_match',
            message: 'Nazwisko panieńskie = nazwisko dziecka',
            hint: 'Sprawdź kontekst: dziecko nieślubne? zbieg okoliczności?',
            field: 'motherSurname'
        });
    }
    
    // ========================================
    // REGUŁA 3: Brak danych (x, .., ?)
    // ========================================
    
    // Ojciec nieznany
    if (record.fatherName === 'x' || record.fatherName === '..' || record.fatherName === '?') {
        record.fatherName = '';
        record.fatherSurname = '';
        record.fatherUnknown = true;
        
        warnings.push({
            type: 'unknown_father',
            message: 'Ojciec nieznany',
            hint: 'Dziecko nieślubne lub ojciec nie wymieniony w akcie',
            field: 'fatherName'
        });
    }
    
    // Matka nieznana (rzadkie)
    if (record.motherName === 'x' || record.motherName === '..' || record.motherName === '?') {
        record.motherName = '';
        record.motherSurname = '';
        record.motherUnknown = true;
        
        warnings.push({
            type: 'unknown_mother',
            message: 'Matka nieznana',
            hint: 'Nietypowy przypadek - sprawdź oryginał aktu',
            field: 'motherName'
        });
    }
    
    // Zwróć rekord z ostrzeżeniami
    record.inferenceWarnings = warnings;
    return record;
}

/**
 * Kolorowanie komórek z ostrzeżeniami
 */
function applySurnameWarnings(td, record, field) {
    const warnings = record.inferenceWarnings || [];
    const warning = warnings.find(w => w.field === field);
    
    if (warning) {
        td.classList.add('cell-warning');
        td.title = `⚠️ ${warning.message}\n${warning.hint}`;
        
        // Dodaj ikonę ostrzeżenia
        const icon = document.createElement('span');
        icon.className = 'warning-icon';
        icon.textContent = '⚠️';
        td.appendChild(icon);
    }
}
```

**CSS dla ostrzeżeń:**
```css
.cell-warning {
    background: #fff3cd !important;
    border-left: 3px solid #ffc107;
    position: relative;
}

.warning-icon {
    position: absolute;
    top: 2px;
    right: 2px;
    font-size: 0.8rem;
}

.cell-warning:hover::after {
    content: attr(title);
    position: absolute;
    bottom: 100%;
    left: 50%;
    transform: translateX(-50%);
    background: #333;
    color: white;
    padding: 0.5rem;
    border-radius: 4px;
    white-space: pre-line;
    z-index: 100;
    max-width: 250px;
    font-size: 0.85rem;
}
```

---

### Problem 5: BADGE "🔒 ORG" dla bezpieczeństwa

**Dodaj wyraźny wskaźnik zachowania danych:**

```javascript
function createTableRow(record, status) {
    const tr = document.createElement('tr');
    
    // ... inne kolumny ...
    
    // Kolumna ORG z badge'm
    const tdOrg = document.createElement('td');
    tdOrg.className = 'col-original';
    tdOrg.innerHTML = `
        <button class="btn-original" onclick="showOriginalModal('${record.id}')">
            <span class="protected-icon">🔒</span> ORG
        </button>
    `;
    tr.appendChild(tdOrg);
    
    return tr;
}

function showOriginalModal(recordId) {
    const record = allData.find(r => r.id === recordId);
    if (!record) return;
    
    // Zamień TAB na | dla czytelności
    const formatted = record.original.replace(/\t/g, ' | ');
    
    const modal = document.getElementById('originalModal');
    document.getElementById('originalText').textContent = formatted;
    modal.style.display = 'flex';
}

function copyOriginalToClipboard() {
    const text = document.getElementById('originalText').textContent;
    navigator.clipboard.writeText(text).then(() => {
        showNotification('Skopiowano oryginalną linię!', 'success');
    });
}
```

**CSS:**
```css
.btn-original {
    display: inline-flex;
    align-items: center;
    gap: 0.25rem;
    padding: 0.25rem 0.5rem;
    border: 1px solid #28a745;
    background: #f0fff4;
    color: #28a745;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.85rem;
    transition: all 0.2s;
}

.btn-original:hover {
    background: #28a745;
    color: white;
    transform: translateY(-1px);
}

.protected-icon {
    font-size: 0.9rem;
}
```

---

## 📋 PLAN WDROŻENIA

### Faza 1: Quick Wins (2h)
1. ✅ **Onboarding modal** (1h)
   - Modal z 4 opcjami + przykład transformacji
   - localStorage dla "nie pokazuj więcej"
   
2. ✅ **Toggle ikona fix** (15min)
   - Dynamiczna ikona (expand_more ↔ expand_less)
   - Zmiana tekstu ("Pokaż" ↔ "Ukryj")
   
3. ✅ **Badge 🔒 ORG** (30min)
   - Button w kolumnie ORG
   - Modal z pełną oryginalną linią
   - Przycisk "Kopiuj"
   
4. ✅ **Ostrzeżenia w UI** (15min)
   - Tooltips z kontekstem
   - Kolorowanie żółte dla ostrzeżeń

### Faza 2: Logika nazwisk (2-3h)
5. ✅ **Implementacja 3 reguł** (2h)
   - Reguła 1: Nazwisko ojca z dziecka
   - Reguła 2: NIE kopiuj nazwiska do matki
   - Reguła 3: Obsługa x/.../? 
   
6. ✅ **Testy logiki** (1h)
   - Przypadki testowe (nieślubne, zbieg okoliczności, brak danych)
   - Walidacja ostrzeżeń

### Faza 3: Mapowanie kolumn (4-5h)
7. ✅ **Auto-detekcja kolumn** (2h)
   - Regex dla ID, dat, imion
   - Sprawdzanie w bazach nazwisk
   
8. ✅ **Drag & drop mapping** (2h)
   - UI podobny do paste/mapper.js
   - Zapisywanie w localStorage
   
9. ✅ **Obsługa różnych typów aktów** (1h)
   - Chrzty, małżeństwa, zgony
   - Różne liczby kolumn (5-50+)

**Całkowity czas: 8-10h**

---

## 🎯 OCZEKIWANE REZULTATY

### Przed wdrożeniem:
- ❌ Użytkownik nie wie od czego zacząć (7 przycisków bez hierarchii)
- ❌ Logika nazwisk zbyt uproszczona (automatyczne kopiowanie)
- ❌ Sztywne 14 kolumn (nie obsługuje małżeństw/zgonów)
- ❌ Brak ostrzeżeń kontekstowych (dziecko nieślubne?)

### Po wdrożeniu:
- ✅ Onboarding z 4 opcjami + przykład (jasny start)
- ✅ 3 reguły nazwisk z ostrzeżeniami kontekstowymi
- ✅ Dynamiczne kolumny 5-50+ (uniwersalne dla wszystkich aktów)
- ✅ Badge 🔒 ORG + modal z pełną oryginalną linią

### Metryki sukcesu:
- **Time to First Action**: 30s → **10s** (onboarding)
- **Surname Logic Accuracy**: 70% → **95%** (3 reguły + ostrzeżenia)
- **Format Support**: 1 (chrzty) → **3+** (chrzty/małżeństwa/zgony)
- **Data Loss Risk**: Średnie → **Zerowe** (badge 🔒 + ORG zawsze widoczne)

---

## 💡 DODATKOWE UWAGI

### Zachowanie kompatybilności wstecznej:
- ✅ Stara struktura 14 kolumn nadal działa
- ✅ Nowe mapowanie opcjonalne (auto-detekcja sugeruje)
- ✅ localStorage migracja (stare dane + nowe pola)

### Testowanie:
1. **Test 1**: Załaduj chrzty (14 kolumn) - sprawdź logikę nazwisk
2. **Test 2**: Załaduj małżeństwa (20 kolumn) - sprawdź mapowanie
3. **Test 3**: Przypadki brzegowe (x, .., dziecko nieślubne)
4. **Test 4**: Onboarding dla nowego użytkownika
5. **Test 5**: Badge 🔒 ORG - kopiowanie oryginalnej linii

### Bezpieczeństwo:
- ✅ NIGDY nie usuwaj kolumny ORG
- ✅ ZAWSZE zapisuj oryginał w formacie `\t` → `|`
- ✅ Ostrzegaj przed utratą danych (backup w localStorage)
