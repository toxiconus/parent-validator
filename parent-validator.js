// ==================== ZMIENNE GLOBALNE ====================
let allData = [];
let nameDatabase = {
    maleNames: new Set(),
    femaleNames: new Set(),
    allNames: new Set(),
    maleSurnames: new Set(),
    femaleSurnames: new Set(),
    allSurnames: new Set()
};
let currentEditingRecord = null;
let tableControlsExpanded = false; // Stan toggle'a opcji

// ==================== TOGGLE TABLE CONTROLS ====================
function toggleTableControls() {
    tableControlsExpanded = !tableControlsExpanded;
    const filterGroup = document.getElementById('filterGroup');
    const actionGroup = document.getElementById('actionGroup');
    const toggleBtn = document.querySelector('.btn-toggle-controls');
    
    if (tableControlsExpanded) {
        filterGroup.style.display = 'grid';
        actionGroup.style.display = 'flex';
        toggleBtn.classList.add('expanded');
    } else {
        filterGroup.style.display = 'none';
        actionGroup.style.display = 'none';
        toggleBtn.classList.remove('expanded');
    }
}

// ==================== INICJALIZACJA ====================
document.addEventListener('DOMContentLoaded', function() {
    console.log('Inicjalizacja edytora...');
    loadNameDatabase();
    checkBackendStatus().then(() => {
        // Załaduj modal PRZED setupem event listeners
        loadEditModal().then(() => {
            setupEventListeners();
            console.log('✅ Inicjalizacja zakończona pomyślnie');
            
            // Auto-ładowanie pliku Ur Blin ORG.txt
            autoLoadDefaultFile();
        });
    });
    
    // Sprawdź czy są zapisane dane w localStorage
    const savedData = localStorage.getItem('agene_parent_data');
    if (savedData) {
        try {
            const parsedData = JSON.parse(savedData);
            if (parsedData.length > 0) {
                // Nie ładuj automatycznie - tylko pokaż komunikat
                showNotification(`Znaleziono ${parsedData.length} zapisanych rekordów. Kliknij "Załaduj przykład" → "Przywróć zapisane" aby je wczytać.`, 'info');
            }
        } catch (err) {
            console.error('Błąd sprawdzania localStorage:', err);
        }
    }
});

// ==================== AUTO-ŁADOWANIE PLIKU ====================
function autoLoadDefaultFile() {
    // Spróbuj załadować plik Ur Blin ORG.txt
    fetch('Ur Blin ORG.txt')
        .then(response => {
            if (!response.ok) throw new Error('Plik nie znaleziony');
            return response.text();
        })
        .then(text => {
            console.log('Auto-załadowano Ur Blin ORG.txt do textarea');
            const textarea = document.getElementById('pasteTextarea');
            if (textarea) {
                textarea.value = text;
                detectAndHintFormat(text);
                updateInputPreview(text);
            }
        })
        .catch(err => {
            console.log('⚠️ Brak pliku Ur Blin ORG.txt - użyj Ctrl+V aby wkleić dane');
        });
}

// ==================== ŁADOWANIE MODALA Z ZEWNĘTRZNEGO PLIKU ====================
function loadEditModal() {
    return fetch('edit-modal.html')
        .then(response => response.text())
        .then(html => {
            document.getElementById('modalContainer').innerHTML = html;
            console.log('Modal edycji załadowany z edit-modal.html');
        })
        .catch(err => {
            console.error('Błąd ładowania modala:', err);
            // Fallback: wstrzyknij modal inline, aby UI działał offline/bez serwera plików
            const container = document.getElementById('modalContainer');
            if (container) {
                container.innerHTML = getEditModalFallbackHtml();
                showNotification('Załadowano modal z fallbacku (brak pliku edit-modal.html)', 'warning');
            } else {
                showNotification('Błąd ładowania modala edycji', 'error');
            }
        });
}

// Fallback HTML modala (gdy fetch edit-modal.html się nie powiedzie)
function getEditModalFallbackHtml() {
        return `
<!-- Modal edycji rekordu (fallback inline) -->
<div class="modal-overlay" id="editModal">
    <div class="modal-content modal-fullscreen">
        <div class="modal-header">
            <h2>Edycja rekordu <span id="modalRecordId"></span></h2>
            <button class="close-btn" onclick="closeEditModal()">×</button>
        </div>
        <div class="modal-body">
            <div class="original-text-section">
                <div class="section-header">
                    <span class="material-icons">description</span>
                    <span>ORYGINALNY TEKST (TSV z | separatorami)</span>
                </div>
                <div class="original-text-display" id="originalTextDisplay"></div>
            </div>
            <form id="editForm">
                <div class="top-bar">
                    <div class="top-bar-item">
                        <label>ROK</label>
                        <input type="text" id="editYear">
                    </div>
                    <div class="top-bar-item">
                        <label>Miejscowosc</label>
                        <input type="text" id="editPlace">
                    </div>
                    <div class="top-bar-item">
                        <label>Nr aktu</label>
                        <input type="text" id="editNumber">
                    </div>
                    <div class="top-bar-item">
                        <label>ID (readonly)</label>
                        <input type="text" id="editID" readonly>
                    </div>
                </div>
                <div class="form-section compact">
                    <div class="section-title">📋 Dziecko</div>
                    <div class="form-row compact-row">
                        <div class="form-group">
                            <label>Nazwisko <span class="validation-indicator" id="validChildSurname"></span></label>
                            <input type="text" id="editSurname">
                        </div>
                        <div class="form-group">
                            <label>Imie <span class="validation-indicator" id="validChildName"></span></label>
                            <input type="text" id="editName">
                        </div>
                    </div>
                </div>
                <div class="parents-container">
                    <div class="parent-section parent-left">
                        <h3 class="parent-title">👨 Ojciec</h3>
                        <div class="form-group">
                            <label>Imie <span class="validation-indicator" id="validFatherName"></span></label>
                            <input type="text" id="editFatherName" placeholder="np. Jozef">
                        </div>
                        <div class="form-group">
                            <label>Nazwisko <span class="validation-indicator" id="validFatherSurname"></span></label>
                            <input type="text" id="editFatherSurname" placeholder="np. Kowalski">
                        </div>
                        <div class="form-group">
                            <label>Wiek</label>
                            <input type="text" id="editFatherAge" placeholder="np. 35">
                        </div>
                    </div>
                    <div class="parent-section parent-right">
                        <h3 class="parent-title">👩 Matka</h3>
                        <div class="form-group">
                            <label>Imie <span class="validation-indicator" id="validMotherName"></span></label>
                            <input type="text" id="editMotherName" placeholder="np. Anna">
                        </div>
                        <div class="form-group">
                            <label>Nazwisko panienskie <span class="validation-indicator" id="validMotherSurname"></span></label>
                            <input type="text" id="editMotherSurname" placeholder="np. Nowak">
                        </div>
                        <div class="form-group">
                            <label>Wiek</label>
                            <input type="text" id="editMotherAge" placeholder="np. 30">
                        </div>
                    </div>
                </div>
                <div class="form-section notes-section">
                    <div class="form-row">
                        <div class="form-group full-width">
                            <label>Uwagi</label>
                            <textarea id="editNotes" rows="2" placeholder="Dodatkowe informacje..."></textarea>
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="form-group full-width">
                            <label>UWAGI ORG (read-only - pelna linia TSV)</label>
                            <textarea id="editOriginalNotes" rows="2" readonly placeholder="Oryginalne dane (tylko do odczytu)"></textarea>
                        </div>
                    </div>
                </div>
                <div class="form-actions">
                    <button type="submit" class="btn btn-primary">
                        <span class="material-icons">save</span> Zapisz zmiany
                    </button>
                    <button type="button" class="btn btn-secondary" onclick="closeEditModal()">
                        <span class="material-icons">close</span> Anuluj
                    </button>
                </div>
            </form>
        </div>
    </div>
</div>
`;
}

// ==================== ŁADOWANIE BAZY NAZW ====================
function loadNameDatabase() {
    const files = [
        'imiona_meskie.json', 'imiona_zenskie.json', 'imiona_wszystkie.json',
        'nazwiska_meskie.json', 'nazwiska_zenskie.json', 'nazwiska_wszystkie.json'
    ];
    const keys = ['maleNames', 'femaleNames', 'allNames', 'maleSurnames', 'femaleSurnames', 'allSurnames'];

    files.forEach((file, i) => {
        fetch(`../../../data/${file}`)
            .then(r => r.ok ? r.json() : [])
            .then(data => {
                if (Array.isArray(data)) {
                    nameDatabase[keys[i]] = new Set(data.map(item => item.trim().toLowerCase()));
                    console.log(`Załadowano ${keys[i]}: ${data.length} elementów`);
                }
            })
            .catch(err => console.warn(`Błąd ładowania ${file}:`, err));
    });
}

// ==================== EVENT LISTENERS ====================
function setupEventListeners() {
    const fileInput = document.getElementById('fileInput');
    const filterRed = document.getElementById('filterRed');
    const filterGreen = document.getElementById('filterGreen');
    const filterGray = document.getElementById('filterGray');
    const editForm = document.getElementById('editForm');
    const pasteTextarea = document.getElementById('pasteTextarea');
    const parseButton = document.getElementById('parseButton');
    const exportBtn = document.getElementById('exportBtn');
    const saveBtn = document.getElementById('saveBtn');

    if (!filterRed || !filterGreen || !filterGray) {
        console.error('Błąd inicjalizacji: Brakuje głównych elementów HTML (filtry)!');
        return;
    }
    
    if (!editForm) {
        console.warn('⚠️ editForm nie znaleziony - modal może nie być załadowany');
    }
    
    if (!pasteTextarea) {
        console.error('Błąd inicjalizacji: Brakuje pasteTextarea!');
        return;
    }

    if (!parseButton) {
        console.error('Błąd inicjalizacji: Brakuje parseButton!');
        return;
    }

    if (!exportBtn) {
        console.error('Błąd inicjalizacji: Brakuje exportBtn!');
        return;
    }

    if (!saveBtn) {
        console.error('Błąd inicjalizacji: Brakuje saveBtn!');
        return;
    }

    // Ctrl+O - otwórz plik
    document.addEventListener('keydown', (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key === 'o') {
            e.preventDefault();
            const input = document.createElement('input');
            input.type = 'file';
            input.accept = '.txt,.tsv,.csv,.json';
            input.onchange = (ev) => {
                const file = ev.target.files[0];
                if (file) {
                    const reader = new FileReader();
                    reader.onload = (re) => {
                        pasteTextarea.value = re.target.result;
                        detectAndHintFormat(re.target.result);
                        updateInputPreview(re.target.result);
                    };
                    reader.readAsText(file);
                }
            };
            input.click();
        }
    });

    filterRed.addEventListener('change', () => generateTableWithBackend());
    filterGreen.addEventListener('change', () => generateTableWithBackend());
    filterGray.addEventListener('change', () => generateTableWithBackend());
    
    // Przycisk parsowania danych
    parseButton.addEventListener('click', () => {
        const text = document.getElementById('pasteTextarea').value.trim();
        if (text) {
            parseDataWithFormatDetection(text);
        } else {
            showNotification('Brak danych do parsowania', 'warning');
        }
    });
    
    // Przycisk eksportu danych
    exportBtn.addEventListener('click', () => exportData());
    
    // Przycisk zapisywania danych
    saveBtn.addEventListener('click', () => saveToLocalStorage());
    
    // editForm musi być podpięty PO załadowaniu modala
    if (editForm) {
        editForm.addEventListener('submit', handleFormSubmit);
    }

    pasteTextarea.addEventListener('paste', () => setTimeout(() => {
        detectAndHintFormat(pasteTextarea.value);
        updateInputPreview(pasteTextarea.value);
    }, 100));
    pasteTextarea.addEventListener('input', () => {
        detectAndHintFormat(pasteTextarea.value);
        updateInputPreview(pasteTextarea.value);
    });
    pasteTextarea.addEventListener('drop', handleDrop);
    pasteTextarea.addEventListener('dragover', e => e.preventDefault());

    // Live validation dla pól edytora
    const fieldsToValidate = [
        'editSurname', 'editName',
        'editFatherName', 'editFatherSurname',
        'editMotherName', 'editMotherSurname'
    ];
    
    fieldsToValidate.forEach(fieldId => {
        const field = document.getElementById(fieldId);
        if (field) {
            field.addEventListener('input', () => {
                // Prosta walidacja na żywo - podświetlanie zielone/czerwone
                const value = field.value.trim();
                if (value.length > 0) {
                    const isValid = validateFieldValue(fieldId, value);
                    field.style.borderColor = isValid ? '#28a745' : '#dc3545';
                } else {
                    field.style.borderColor = '#ddd';
                }
            });
        }
    });

    console.log('Event listeners zainstalowane pomyślnie');
}

// ==================== WALIDACJA POLA NA ŻYWO ====================
function validateFieldValue(fieldId, value) {
    if (!value || value.length < 2) return false;
    
    const lowerValue = value.toLowerCase();
    
    // Sprawdź odpowiednie bazy danych w zależności od pola
    if (fieldId.includes('Name')) {
        return allNames.has(lowerValue) || allSurnames.has(lowerValue);
    } else if (fieldId.includes('Surname')) {
        return allSurnames.has(lowerValue);
    }
    
    return false;
}

// ==================== PODGLĄD DANYCH WEJŚCIOWYCH ====================
function updateInputPreview(text) {
    const previewDiv = document.getElementById('inputPreview');
    const previewTable = document.getElementById('previewTable');
    const previewTableHead = document.getElementById('previewTableHead');
    const previewTableBody = document.getElementById('previewTableBody');
    const previewRowCount = document.getElementById('previewRowCount');
    const previewColCount = document.getElementById('previewColCount');
    
    if (!text || !text.trim()) {
        previewDiv.style.display = 'none';
        return;
    }
    
    const separator = detectSeparator(text);
    const lines = text.trim().split('\n').filter(l => l.trim());
    
    if (lines.length === 0) {
        previewDiv.style.display = 'none';
        return;
    }
    
    // Wykryj czy pierwszy wiersz to nagłówki
    const firstLine = lines[0].split(separator);
    const hasHeaders = firstLine[0].toLowerCase().includes('id') || 
                      firstLine.some(cell => cell.toLowerCase().includes('nazwisko') || 
                                            cell.toLowerCase().includes('imię') ||
                                            cell.toLowerCase().includes('rok'));
    
    const dataStartIndex = hasHeaders ? 1 : 0;
    const maxRows = Math.min(100, lines.length - dataStartIndex); // Pokaż max 100 wierszy
    
    // Generuj nagłówki
    previewTableHead.innerHTML = '';
    const headerRow = document.createElement('tr');
    const colCount = firstLine.length;
    
    for (let i = 0; i < colCount; i++) {
        const th = document.createElement('th');
        th.textContent = hasHeaders ? firstLine[i] : `Kol ${i+1}`;
        headerRow.appendChild(th);
    }
    previewTableHead.appendChild(headerRow);
    
    // Generuj wiersze danych
    previewTableBody.innerHTML = '';
    for (let i = dataStartIndex; i < dataStartIndex + maxRows; i++) {
        if (i >= lines.length) break;
        
        const cells = lines[i].split(separator);
        const row = document.createElement('tr');
        
        for (let j = 0; j < colCount; j++) {
            const td = document.createElement('td');
            const value = cells[j] || '';
            td.textContent = value;
            
            // Kolorowanie na podstawie bazy - próbuj wykryć czy to imię/nazwisko
            if (value && value.trim().length > 0 && value !== '-') {
                const normalized = value.trim().toLowerCase();
                if (nameDatabase.allNames && nameDatabase.allNames.has(normalized)) {
                    td.classList.add('text-validated');
                } else if (nameDatabase.allSurnames && nameDatabase.allSurnames.has(normalized)) {
                    td.classList.add('text-validated');
                } else if (value.length > 2 && /^[a-zA-ZąćęłńóśźżĄĆĘŁŃÓŚŹŻ]+$/.test(value)) {
                    // Jeśli wygląda jak nazwa (tylko litery) ale nie ma w bazie
                    td.classList.add('cell-not-found');
                }
            }
            
            row.appendChild(td);
        }
        
        previewTableBody.appendChild(row);
    }
    
    // Aktualizuj liczniki
    const totalDataRows = lines.length - (hasHeaders ? 1 : 0);
    previewRowCount.textContent = totalDataRows;
    previewColCount.textContent = colCount;
    
    previewDiv.style.display = 'block';
}

// ==================== WKLEJANIE I UPUSZCZANIE ====================
function handleDrop(e) {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file && (file.type === 'text/plain' || file.name.match(/\.(txt|tsv|csv)$/i))) {
        const reader = new FileReader();
        reader.onload = ev => {
            document.getElementById('pasteTextarea').value = ev.target.result;
            detectAndHintFormat(ev.target.result);
            updateInputPreview(ev.target.result);
        };
        reader.readAsText(file);
    }
}

function detectAndHintFormat(text) {
    if (!text.trim()) {
        const hint = document.getElementById('formatHint');
        if (hint) {
            hint.textContent = '';
            hint.style.display = 'none';
        }
        return;
    }

    const separator = detectSeparator(text);
    const lines = text.trim().split('\n');
    const colCount = lines[0].split(separator).length;

    const names = { '\t': 'TAB', ',': 'CSV', ';': 'Średnik', '|': 'Pionowa kreska' };
    const hint = document.getElementById('formatHint');
    if (hint) {
        hint.textContent = `Wykryto: ${names[separator] || 'Inny'} (${colCount} kolumn)`;
        hint.style.display = 'inline-flex';
    }
}

function detectSeparator(text) {
    const lines = text.split('\n').slice(0, 5).filter(l => l.trim());
    if (lines.length === 0) return '\t';

    const counts = { '\t': 0, ',': 0, ';': 0, '|': 0 };
    lines.forEach(line => {
        for (const sep of Object.keys(counts)) {
            counts[sep] += (line.split(sep).length - 1);
        }
    });

    // Najczęstszy separator
    const bestSep = Object.entries(counts).sort((a, b) => b[1] - a[1])[0][0];
    
    // Jeśli TAB ma przynajmniej kilka kolumn, użyj TAB
    if (bestSep === '\t' && counts['\t'] > 0) {
        return '\t';
    }
    
    // W przeciwnym razie użyj najlepszego
    return bestSep || '\t';
}

// ==================== PARSOWANIE DANYCH ====================
async function parseAndLoadPastedData() {
    const textarea = document.getElementById('pasteTextarea');
    const text = textarea.value.trim();
    
    if (!text) {
        showNotification('Pole jest puste.', 'warning');
        return;
    }

    // WYCZYŚĆ STARE DANE PRZED PARSOWANIEM NOWYCH!
    allData = [];
    console.log('Wyczyszczono stare dane. Parsowanie nowych...');

    const separator = detectSeparator(text);
    
    try {
        console.log('Rozpoczynam parsowanie... separator:', JSON.stringify(separator));
        await parseDataWithFormatDetection(text, separator);
        console.log('Po parseDataWithFormatDetection, allData.length =', allData.length);
        
        if (allData.length === 0) {
            console.warn('Brak danych po parsowaniu - sprawdzam separator');
            // Spróbuj inny separator
            const altSeparator = separator === '\t' ? ',' : '\t';
            await parseDataWithFormatDetection(text, altSeparator);
        }
        
        console.log('Wyświetlam dane... allData.length =', allData.length);
        if (allData.length > 0) {
            console.log('Przykładowy rekord:', allData[0]);
        }
        displayData();
        showNotification(`Załadowano ${allData.length} rekordów`, 'success');
        
        // Nie czyszczmy - może user chce edytować
        // textarea.value = '';
        
        // Przewiń do tabeli
        const tableWrapper = document.getElementById('tableWrapper');
        if (tableWrapper) {
            setTimeout(() => tableWrapper.scrollIntoView({ behavior: 'smooth' }), 300);
        }
    } catch (error) {
        console.error('Błąd parsowania:', error);
        showNotification('Błąd parsowania danych: ' + error.message, 'error');
    }
}

function clearPasteArea() {
    document.getElementById('pasteTextarea').value = '';
    const hint = document.getElementById('formatHint');
    if (hint) {
        hint.textContent = '';
        hint.style.display = 'none';
    }
    // Ukryj podgląd
    const previewDiv = document.getElementById('inputPreview');
    if (previewDiv) {
        previewDiv.style.display = 'none';
    }
}

// ==================== ŁADOWANIE PLIKÓW ====================
function loadDataFile() {
    document.getElementById('fileInput').click();
}

function handleFileSelect(e) {
    const file = e.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = ev => {
        try {
            parseDataWithFormatDetection(ev.target.result);
            displayData();
            showNotification(`Załadowano plik: ${file.name} (${allData.length} rekordów)`, 'success');
        } catch (error) {
            showNotification('Błąd parsowania pliku', 'warning');
            console.error(error);
        }
    };
    reader.readAsText(file, 'UTF-8');
}

async function loadExampleData() {
    // Sprawdź czy są zapisane dane
    const savedData = localStorage.getItem('agene_parent_data');
    if (savedData) {
        try {
            const parsedData = JSON.parse(savedData);
            if (parsedData.length > 0) {
                // Zapytaj użytkownika
                if (confirm(`Znaleziono ${parsedData.length} zapisanych rekordów w pamięci.\n\nKliknij OK aby przywrócić zapisane dane\nlub Anuluj aby załadować przykładowe dane testowe.`)) {
                    loadSavedData();
                    return;
                }
            }
        } catch (err) {
            console.error('Błąd sprawdzania localStorage:', err);
        }
    }
    
    // Załaduj przykładowe dane
    const example = `ID	Nazwisko	Imię	Nr	Rok	Data	Miejsce	Imię ojca	Nazwisko ojca	Imię matki	Nazwisko matki	Uwagi
CH.LUB.BLIN.0001574	Zyśko	Zofia	1	1841	10.01	Moczydła	Józef	Zyśko	Marianna	Kasperek	
CH.LUB.BLIN.0001575	Zdebel	Paweł	2	1841	22.01	Blinów	X	X	Magdalena	Zdebel	ojciec nieznany
CH.LUB.BLIN.0001528	Jachura	Stanisław	3	1840			Brzozówka , Jan i Franciszka Stępień`;
    
    allData = []; // Wyczyść stare dane
    await parseDataWithFormatDetection(example, '\t');
    displayData();
    showNotification('Załadowano dane przykładowe', 'success');
}

function loadSavedData() {
    const savedData = localStorage.getItem('agene_parent_data');
    if (!savedData) {
        showNotification('Brak zapisanych danych w pamięci', 'warning');
        return;
    }
    
    try {
        allData = JSON.parse(savedData);
        if (allData.length > 0) {
            displayData();
            showNotification(`Przywrócono ${allData.length} rekordów z pamięci przeglądarki`, 'success');
        } else {
            showNotification('Zapisane dane są puste', 'warning');
        }
    } catch (err) {
        console.error('Błąd ładowania danych z localStorage:', err);
        showNotification('Błąd podczas ładowania zapisanych danych', 'error');
    }
}

async function loadParserResults() {
    try {
        showNotification('Ładuję dane z parsera...', 'info');
        const res = await fetch('./parser_v2_results.json');
        if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`);
        
        const data = await res.json();
        
        allData = data.map(r => ({
            id: r.record_id || '',
            surname: '',
            name: '',
            year: '',
            place: r.parent_data.origin_place || '',
            fatherName: r.parent_data.father_name || '',
            fatherSurname: r.parent_data.father_surname || '',
            motherName: r.parent_data.mother_name || '',
            motherSurname: r.parent_data.mother_surname || '',
            motherMaidenName: r.parent_data.mother_surname || '',
            notes: r.warnings?.join('; ') || '',
            original: r.original_text || r.raw_text || '',
            fatherNameValidated: false,
            fatherSurnameValidated: false,
            motherNameValidated: false,
            motherSurnameValidated: false,
            motherMaidenNameValidated: false
        }));
        
        allData.forEach(validateRecord);
        displayData();
        showNotification(`Załadowano ${allData.length} rekordów z parsera`, 'success');
    } catch (err) {
        console.error('Błąd ładowania parsera:', err);
        showNotification('Nie można załadować parser_v2_results.json', 'warning');
    }
}

// ==================== PARSOWANIE DANYCH Z FORMATU TSV ====================
async function parseDataWithFormatDetection(content, separator = '\t') {
    const lines = content.split('\n')
        .map(l => l.trim())
        .filter(l => l && !l.startsWith('//') && !l.startsWith('#'));
    
    if (lines.length === 0) {
        allData = [];
        return;
    }

    // Spróbuj użyć Python backend (jeśli działa)
    try {
        const response = await fetch('http://localhost:5000/api/parse', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ data: content, delimiter: separator })
        });
        
        if (response.ok) {
            const result = await response.json();
            if (result.success && result.records) {
                console.log('✅ Parsowanie przez Python backend', result.records.length, 'rekordów');
                allData = result.records.map(r => ({
                    id: r.record_id || '',
                    surname: r.parent_data?.surname || r.parent_data?.father_surname || '',
                    name: r.parent_data?.name || r.parent_data?.father_name || '',
                    year: r.parent_data?.year || '',
                    number: r.parent_data?.number || '',
                    place: r.parent_data?.origin_place || '',
                    fatherName: r.parent_data?.father_name || '',
                    fatherSurname: r.parent_data?.father_surname || '',
                    fatherAge: r.parent_data?.father_age || '',
                    motherName: r.parent_data?.mother_name || '',
                    motherSurname: r.parent_data?.mother_surname || '',
                    motherAge: r.parent_data?.mother_age || '',
                    motherMaidenName: r.parent_data?.mother_surname || '',
                    notes: r.parent_data?.notes || r.warnings?.join('; ') || '',
                    original: r.original_text || '',
                    fatherNameValidated: r.validation?.father_name_valid || false,
                    fatherSurnameValidated: r.validation?.father_surname_valid || false,
                    motherNameValidated: r.validation?.mother_name_valid || false,
                    motherSurnameValidated: r.validation?.mother_surname_valid || false,
                    motherMaidenNameValidated: r.validation?.mother_surname_valid || false
                }));
                console.log('✅ Dane sparsowane przez backend, wywołuję displayData()');
                displayData();
                return;
            }
        }
    } catch (err) {
        console.warn('⚠️ Python backend niedostępny, używam JavaScript parsera:', err.message);
    }
    
    // Fallback: lokalny JavaScript parser
    console.log('📝 Parsowanie lokalnie (JavaScript Parser V2)');
    parseDataLocalFallback(content, separator);
}

function parseDataLocalFallback(content, separator = '\t') {
    /**
     * Fallback parser JavaScript - gdy backend jest niedostępny
     */
    const lines = content.split('\n')
        .map(l => l.trim())
        .filter(l => l && !l.startsWith('//') && !l.startsWith('#'));
    
    if (lines.length === 0) {
        allData = [];
        showNotification('Brak danych do parsowania', 'warning');
        return;
    }

    const firstLine = lines[0];
    const hasHeaders = firstLine.toLowerCase().includes('id') || 
                      firstLine.toLowerCase().includes('nazwisko') ||
                      firstLine.toLowerCase().includes('imię');
    
    const dataLines = hasHeaders ? lines.slice(1) : lines;
    
    // Sprawdzenie czy kolumna ID (0) ma wartości
    let hasIDs = false;
    if (dataLines.length > 0) {
        const firstDataLine = dataLines[0].split(separator);
        hasIDs = firstDataLine[0] && firstDataLine[0].trim() !== '';
    }
    
    console.log('parseDataLocalFallback: hasIDs=', hasIDs, 'dataLines.length=', dataLines.length);
    
    // Jeśli brakuje ID, parsuj z autogenerowaniem ID
    if (!hasIDs && dataLines.length > 0) {
        console.log('Brak ID w kolumnie 0 - autogenerujemy');
        parseDataWithIds(dataLines, separator, -1);
        return;
    }
    
    // Jeśli mamy ID, parsuj normalnie
    parseDataWithBackend(dataLines, separator);
}

// ==================== STATYSTYKI Z BACKENDU ====================
function updateStatsFromBackend(backendStats) {
    document.getElementById('recordCount').textContent = backendStats.total;
    document.getElementById('confirmedCount').textContent = backendStats.confirmed;
    document.getElementById('warningCount').textContent = backendStats.warning;
    document.getElementById('progressPercent').textContent = `${backendStats.progress}%`;
    
    // Ustaw progress bar jeśli istnieje
    const progressBar = document.getElementById('progressBar');
    if (progressBar) {
        progressBar.style.width = `${backendStats.progress}%`;
    }
}

// ==================== SPRAWDZANIE BACKENDU ====================
async function checkBackendStatus() {
    try {
        const response = await fetch('http://127.0.0.1:5000/api/health');
        if (response.ok) {
            const data = await response.json();
            console.log('Backend dostępny:', data);
            showNotification('Backend Python połączony', 'success');
            return true;
        }
    } catch (error) {
        console.warn('Backend niedostępny:', error);
        showNotification('Backend Python niedostępny - używam parsowania lokalnego', 'warning');
        return false;
    }
    return false;
}

// ==================== WALIDACJA PRZEZ BACKEND ====================
async function validateWithBackend(records) {
    try {
        const response = await fetch('http://127.0.0.1:5000/api/validate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ records: records })
        });
        
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        
        const result = await response.json();
        if (!result.success) throw new Error(result.error);
        
        // Aktualizuj globalne dane
        allData = result.records;
        
        // Aktualizuj statystyki
        updateStatsFromBackend(result.stats);
        
        return result.records;
    } catch (error) {
        console.error('Błąd walidacji przez backend:', error);
        // Fallback: lokalna walidacja
        return validateRecordsLocal(records);
    }
}

// ==================== GENEROWANIE TABELI PRZEZ BACKEND ====================
async function generateTableWithBackend() {
    console.log('generateTableWithBackend: Rozpoczynam generowanie tabeli, allData.length =', allData.length);
    
    try {
        const filters = {
            red: document.getElementById('filterRed').checked,
            green: document.getElementById('filterGreen').checked,
            gray: document.getElementById('filterGray').checked
        };
        
        console.log('generateTableWithBackend: Wysyłam do backend, filters =', filters);
        
        const response = await fetch('http://127.0.0.1:5000/api/table', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                records: allData,
                filters: filters
            })
        });
        
        console.log('generateTableWithBackend: Odpowiedź backend, status =', response.status);
        
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        
        const result = await response.json();
        console.log('generateTableWithBackend: Odpowiedź JSON =', result);
        
        if (!result.success) throw new Error(result.error);
        
        // Wstaw HTML tabeli
        const tbody = document.getElementById('tableBody');
        console.log('generateTableWithBackend: tbody element =', tbody);
        
        if (tbody) {
            tbody.innerHTML = result.html;
            console.log('generateTableWithBackend: Wstawiono HTML, długość =', result.html.length);
        } else {
            console.error('generateTableWithBackend: Nie znaleziono elementu tableBody!');
        }
        
        // Aktualizuj liczniki
        const filteredCount = document.getElementById('filteredCount');
        const totalCount = document.getElementById('totalCount');
        
        if (filteredCount) filteredCount.textContent = result.filtered_count;
        if (totalCount) totalCount.textContent = result.total_count;
        
        console.log('generateTableWithBackend: Zaktualizowano liczniki, filtered =', result.filtered_count, 'total =', result.total_count);
        
        return result;
    } catch (error) {
        console.error('Błąd generowania tabeli przez backend:', error);
        // Fallback: lokalne generowanie - ale unikaj rekursji
        console.log('generateTableWithBackend: Próba lokalnego generowania tabeli');
        try {
            updateTableDisplay();
        } catch (localError) {
            console.error('Błąd lokalnego generowania tabeli:', localError);
        }
    }
}

// ==================== PARSOWANIE PRZEZ BACKEND ====================
async function parseDataWithBackend(dataLines, separator) {
    try {
        showNotification('Wysyłanie danych do backendu...', 'info');
        
        const response = await fetch('http://127.0.0.1:5000/api/parse', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                data: dataLines.join('\n'),
                delimiter: separator
            })
        });
        
        if (!response.ok) {
            throw new Error(`Błąd HTTP: ${response.status}`);
        }
        
        const result = await response.json();
        
        if (!result.success) {
            throw new Error(result.error || 'Błąd parsowania');
        }
        
        // Konwertuj wyniki backendu na format aplikacji
        allData = result.records.map(r => ({
            id: r.record_id,
            year: r.parent_data.year || '',
            number: r.parent_data.number || '',
            surname: r.parent_data.surname || '',
            name: r.parent_data.name || '',
            place: r.parent_data.place || '',
            fatherName: r.parent_data.father_name || '',
            fatherSurname: r.parent_data.father_surname || '',
            fatherAge: r.parent_data.father_age || '',
            motherName: r.parent_data.mother_name || '',
            motherSurname: r.parent_data.mother_surname || '',
            motherAge: r.parent_data.mother_age || '',
            notes: r.parent_data.notes || '',
            original: r.parent_data.original || '',
            fatherNameValidated: false, // zostanie ustawione przez walidację
            fatherSurnameValidated: false,
            motherNameValidated: false,
            motherSurnameValidated: false,
            motherMaidenNameValidated: false
        }));
        
        // Walidacja przez backend
        await validateWithBackend(allData);
        
        // Aktualizuj statystyki z parsowania
        if (result.stats) {
            updateStatsFromBackend(result.stats);
        }
        
        // Generuj tabelę przez backend
        await generateTableWithBackend();
        
        showNotification(`Załadowano ${allData.length} rekordów z backendu`, 'success');
        
        // Pokaż podsumowanie
        if (result.stats) {
            console.log('Statystyki parsowania:', result.stats);
        }
        
    } catch (error) {
        console.error('Błąd parsowania przez backend:', error);
        showNotification(`Błąd parsowania: ${error.message}`, 'error');
        
        // Fallback: użyj lokalnego parsowania jeśli backend niedostępny
        console.log('Próbuję lokalne parsowanie...');
        parseDataWithIds(dataLines, separator);
    }
}

function parseDataWithIds(dataLines, separator = '\t', idColumnIndex = -1) {
    allData = [];
    
    dataLines.forEach((line, index) => {
        const fields = line.split(separator).map(f => f.trim());
        
        // DEBUG - pokaż pierwsze 3 linie
        if (index < 3) {
            console.log(`Linia ${index}: ${fields.length} pól`, fields);
        }
        
        let record;
        const fieldCount = fields.length;
        
        // Wybierz ID z kolumny lub autogeneruj
        let recordId = '';
        if (idColumnIndex >= 0 && idColumnIndex < fields.length) {
            recordId = fields[idColumnIndex];
        }
        
        // Parsuj dane zależnie od liczby kolumn
        if (fieldCount >= 12) {
            // Rozpoznaj format: fields[1] = rok (cyfry) vs nazwisko (tekst)
            const isNewFormat = /^\d{4}$/.test(fields[1] || '');
            
            if (isNewFormat) {
                // Format "ur nowe blinow.txt": ID|ROK|Nr|Nazwisko|Imię|Miejscowość|ImięO|NazwiskoO|wiekO|IM|NM|wM|[uwagi|UWAGI ORG]
                record = {
                    id: recordId || fields[0] || '',
                    year: fields[1] || '',
                    number: fields[2] || '',
                    surname: fields[3] || '',
                    name: fields[4] || '',
                    place: fields[5] || '',
                    fatherName: fields[6] || '',
                    fatherSurname: fields[7] || '',
                    fatherAge: fields[8] || '',
                    motherName: fields[9] || '',
                    motherSurname: fields[10] || '',
                    motherAge: fields[11] || '',
                    motherMaidenName: fields[10] || '',
                    notes: fields[12] || '',
                    original: line,
                    originalNotes: fields[13] || '',
                    fatherNameValidated: false,
                    fatherSurnameValidated: false,
                    motherNameValidated: false,
                    motherSurnameValidated: false,
                    motherMaidenNameValidated: false
                };
            } else {
                // Stary format rozszerzony: ID|Nazwisko|Imię|Nr|Rok|Data|Miejsce|ImięO|NazwO|wiekO|ImM|NazwM|wiekM|...
                record = {
                    id: recordId || fields[0] || '',
                    surname: fields[1] || '',
                    name: fields[2] || '',
                    number: fields[3] || '',
                    year: fields[4] || '',
                    place: fields[6] || '',
                    fatherName: fields[7] || '',
                    fatherSurname: fields[8] || '',
                    fatherAge: fields[9] || '',
                    motherName: fields[11] || '',
                    motherSurname: fields[12] || '',
                    motherAge: fields[13] || '',
                    motherMaidenName: fields[12] || '',
                    notes: fields[14] || '',
                    original: line,
                    fatherNameValidated: false,
                    fatherSurnameValidated: false,
                    motherNameValidated: false,
                    motherSurnameValidated: false,
                    motherMaidenNameValidated: false
                };
            }
        } else if (fieldCount >= 8) {
            // Stary format: ID|Nazwisko|Imię|Nr|Rok|Data|Miejsce|Uwagi
            // LUB format z genealogią w jednej kolumnie
            const genealogicalString = fields[7] || '';
            
            // Sprawdź czy pole 7 zawiera strukturę genealogiczną (różne wzorce)
            const hasGenealogy = genealogicalString.includes(' i ') || 
                                genealogicalString.includes('s.') || 
                                genealogicalString.includes('c.') ||
                                genealogicalString.includes(' z ') ||
                                genealogicalString.includes('/');
            
            if (hasGenealogy) {
                const genealogical = parseGenealogicalData(genealogicalString);
                
                record = {
                    id: recordId || fields[0] || '',
                    surname: fields[1] || '',
                    name: fields[2] || '',
                    year: fields[4] || fields[3] || '',
                    place: genealogical.place || fields[6] || '',
                    fatherName: genealogical.fatherName || '',
                    fatherSurname: genealogical.fatherSurname || '',
                    motherName: genealogical.motherName || '',
                    motherSurname: genealogical.motherSurname || '',
                    motherMaidenName: genealogical.motherSurname || '',
                    notes: genealogicalString,
                    original: line,
                    fatherNameValidated: false,
                    fatherSurnameValidated: false,
                    motherNameValidated: false,
                    motherSurnameValidated: false,
                    motherMaidenNameValidated: false
                };
            } else {
                // Standardowy stary format
                record = {
                    id: recordId || fields[0] || '',
                    surname: fields[1] || '',
                    name: fields[2] || '',
                    year: fields[4] || '',
                    place: fields[6] || '',
                    fatherName: '',
                    fatherSurname: '',
                    motherName: '',
                    motherSurname: '',
                    motherMaidenName: '',
                    notes: fields[7] || '',
                    original: line,
                    fatherNameValidated: false,
                    fatherSurnameValidated: false,
                    motherNameValidated: false,
                    motherSurnameValidated: false,
                    motherMaidenNameValidated: false
                };
            }
        } else {
            // Krótki format - inteligentne rozpoznawanie
            // Logika: szukaj 4-cyfrowego roku (1000-2500), 1-3 cyfrowego aktu
            let yearValue = '';
            let numberValue = '';
            let idValue = recordId || fields[0] || '';
            let surnameValue = '';
            let nameValue = '';
            
            // REGUŁA: ID typu CH.LUB.BLIN.1908.001 -> 1908=rok, 001=nr aktu
            const idMatch = idValue.match(/\.(\d{4})\.(\d{1,3})$/);
            if (idMatch && fields.length <= 5) {
                yearValue = idMatch[1];
                numberValue = idMatch[2].replace(/^0+/, '') || idMatch[2]; // usuń leading zeros
            }
            
            // Przeszukaj pola w poszukiwaniu roku i numeru aktu
            const numericFields = [];
            const textFields = [];
            
            fields.forEach((field, idx) => {
                if (idx === 0 && idValue) return; // Pomin ID jeśli już mamy
                
                const trimmed = field.trim();
                if (/^\d+$/.test(trimmed)) {
                    numericFields.push({ value: trimmed, index: idx });
                } else if (trimmed) {
                    textFields.push({ value: trimmed, index: idx });
                }
            });
            
            // Rozpoznaj rok (4 cyfry, 1000-2500) - tylko jeśli nie z ID
            if (!yearValue) {
                for (const nf of numericFields) {
                    const num = parseInt(nf.value);
                    if (nf.value.length === 4 && num >= 1000 && num <= 2500) {
                        yearValue = nf.value;
                        break;
                    }
                }
            }
            
            // Rozpoznaj numer aktu (1-3 cyfry, nie rok) - tylko jeśli nie z ID
            if (!numberValue) {
                for (const nf of numericFields) {
                    if (nf.value !== yearValue && nf.value.length <= 3) {
                        numberValue = nf.value;
                        break;
                    }
                }
            }
            
            // Pierwsze dwa pola tekstowe to nazwisko i imię
            if (textFields.length >= 1) surnameValue = textFields[0].value;
            if (textFields.length >= 2) nameValue = textFields[1].value;
            
            record = {
                id: idValue || generateAutoId({ surname: surnameValue, name: nameValue, year: yearValue }, index),
                surname: surnameValue,
                name: nameValue,
                number: numberValue,
                year: yearValue,
                place: '',
                fatherName: '',
                fatherSurname: '',
                motherName: '',
                motherSurname: '',
                motherMaidenName: '',
                notes: '',
                original: line,
                fatherNameValidated: false,
                fatherSurnameValidated: false,
                motherNameValidated: false,
                motherSurnameValidated: false,
                motherMaidenNameValidated: false
            };
        }
        
        // Autogeneruj ID jeśli brakuje
        if (!record.id || record.id.trim() === '') {
            record.id = generateAutoId(record, index);
        }
        
        // Sprawdź czy w polu ojca jest struktura genealogiczna
        if (record.fatherName && record.fatherName.includes(',') && record.fatherName.includes(' i ')) {
            const parsed = parseGenealogicalData(record.fatherName);
            if (parsed.place) record.place = parsed.place;
            if (parsed.fatherName) record.fatherName = parsed.fatherName;
            if (parsed.fatherSurname) record.fatherSurname = parsed.fatherSurname;
            if (parsed.motherName) record.motherName = parsed.motherName;
            if (parsed.motherSurname) record.motherSurname = parsed.motherSurname;
        }
        
        validateRecord(record);
        allData.push(record);
    });
    
    console.log('parseDataWithIds finished: allData.length =', allData.length);
    displayData();
}
// ==================== PARSER TEKSTU GENEALOGICZNEGO ====================
function parseGenealogicalData(text) {
    const result = {
        place: '',
        fatherName: '',
        fatherSurname: '',
        motherName: '',
        motherSurname: ''
    };
    
    // Konwersja form odmienionych -> mianownik używając bazy danych
    const normalizeToNominative = (word, isName = true) => {
        if (!word) return word;
        
        const database = isName ? nameDatabase.allNames : nameDatabase.allSurnames;
        if (!database || database.size === 0) return word;
        
        const lower = word.toLowerCase();
        
        // Jeśli jest w bazie bezpośrednio - zwróć z dużej litery
        if (database.has(lower)) {
            return word.charAt(0).toUpperCase() + lower.slice(1);
        }
        
        // Poszukaj w bazie dopasowania (odmiana dopełniacza)
        for (const baseForm of database) {
            // Dopełniacz imion męskich: -a (Jan->Jana, Maciej->Macieja)
            if (isName && lower === baseForm + 'a' && !baseForm.endsWith('a')) {
                return baseForm.charAt(0).toUpperCase() + baseForm.slice(1);
            }
            // Odmiany końcówek -ej, -i, -y
            if (lower === baseForm.replace(/a$/, 'y') || 
                lower === baseForm.replace(/a$/, 'i') ||
                lower === baseForm + 'ej') {
                return baseForm.charAt(0).toUpperCase() + baseForm.slice(1);
            }
        }
        
        // Historyczne formy nazwisk żeńskich: -ówna, -anka, -ka
        if (!isName) {
            if (lower.endsWith('ówna')) {
                const base = lower.replace(/ówna$/, '');
                if (database.has(base)) {
                    return base.charAt(0).toUpperCase() + base.slice(1);
                }
            }
            if (lower.endsWith('anka')) {
                const base = lower.replace(/anka$/, '');
                if (database.has(base)) {
                    return base.charAt(0).toUpperCase() + base.slice(1);
                }
            }
        }
        
        return word;
    };
    
    // Wzorce genealogiczne:
    // "Blinów / Tomasz l.45 i Antonina Pazdrak l.45"
    // "Blinów - Marcin i Antonina Jachura"
    // "Blinów s. Marcina i Katarzyny z Kurczaków"
    // "Brzozówka c. Wojciecha i Tekli z Dobrzyńskich."
    
    let workText = text.trim();
    
    // Wyciągnij miejscowość (przed / lub - lub s. lub c.)
    const placeMatch = workText.match(/^([^\/-]+?)\s*[\/\-]/) || 
                       workText.match(/^([^\s]+)\s+[sc]\./);
    if (placeMatch) {
        result.place = placeMatch[1].trim();
        workText = workText.substring(placeMatch[0].length).trim();
    }
    
    // Znajdź separator " i "
    if (workText.includes(' i ')) {
        const parts = workText.split(' i ');
        
        // Ojciec (pierwsza część)
        let fatherText = parts[0].trim();
        // Usuń "s.", "c.", "l.XX"
        fatherText = fatherText.replace(/^[sc]\.\s*/, '').replace(/\s+l\.\d+/, '').trim();
        const fatherParts = fatherText.split(/\s+/);
        if (fatherParts.length > 0) result.fatherName = normalizeToNominative(fatherParts[0], true);
        if (fatherParts.length > 1) result.fatherSurname = normalizeToNominative(fatherParts.slice(1).join(' '), false);
        
        // Matka (druga część)
        let motherText = parts[1].trim();
        // Usuń "l.XX" i "z "
        motherText = motherText.replace(/\s+l\.\d+/, '').trim();
        
        // Sprawdź "z XYZ" (nazwisko panieńskie)
        const maidenMatch = motherText.match(/\s+z\s+(.+?)(?:\.|$)/);
        if (maidenMatch) {
            result.motherSurname = normalizeToNominative(maidenMatch[1].trim(), false);
            motherText = motherText.substring(0, motherText.indexOf(' z ')).trim();
        }
        
        const motherParts = motherText.split(/\s+/);
        if (motherParts.length > 0) result.motherName = normalizeToNominative(motherParts[0], true);
        if (!result.motherSurname && motherParts.length > 1) {
            result.motherSurname = normalizeToNominative(motherParts.slice(1).join(' '), false);
        }
    }
    
    return result;
}

// ==================== WALIDACJA ====================
function validateRecord(record) {
    const checkName = (name) => {
        if (!name || name.toLowerCase() === 'x' || name === '?') return false;
        return nameDatabase.allNames.has(name.toLowerCase());
    };
    
    const checkSurname = (surname, type = 'all') => {
        if (!surname || surname.toLowerCase() === 'x' || surname === '?') return false;
        
        if (type === 'male' && nameDatabase.maleSurnames.has(surname.toLowerCase())) return true;
        if (type === 'female' && nameDatabase.femaleSurnames.has(surname.toLowerCase())) return true;
        if (nameDatabase.allSurnames.has(surname.toLowerCase())) return true;
        
        return false;
    };
    
    record.fatherNameValidated = checkName(record.fatherName);
    record.motherNameValidated = checkName(record.motherName);
    record.fatherSurnameValidated = checkSurname(record.fatherSurname, 'male');
    record.motherSurnameValidated = checkSurname(record.motherSurname, 'female');
    record.motherMaidenNameValidated = checkSurname(record.motherMaidenName, 'female');
}

function getRecordStatus(record) {
    const hasData = record.fatherName || record.fatherSurname || record.motherName || record.motherSurname;
    if (!hasData) return 'empty';
    
    const isFullyValidated = record.fatherNameValidated && 
                            record.fatherSurnameValidated && 
                            record.motherNameValidated && 
                            record.motherSurnameValidated;
    
    return isFullyValidated ? 'validated' : 'warning';
}

// ==================== WYŚWIETLANIE ====================
function displayData() {
    if (allData.length === 0) {
        showNotification('Brak danych do wyświetlenia', 'warning');
        return;
    }
    
    const tableWrapper = document.getElementById('tableWrapper');
    const bottomPanel = document.getElementById('bottomPanel');
    
    if (tableWrapper) tableWrapper.style.display = 'block';
    if (bottomPanel) bottomPanel.style.display = 'block';
    
    updateStats();
    generateTableWithBackend();
    
    // Pokaż pierwszy wiersz w okienku
    if (allData.length > 0) {
        showOriginalLine(allData[0]);
    }
}

function updateTableDisplay() {
    const tbody = document.getElementById('tableBody');
    if (!tbody) return;
    
    tbody.innerHTML = '';

    const showRed = document.getElementById('filterRed').checked;
    const showGreen = document.getElementById('filterGreen').checked;
    const showGray = document.getElementById('filterGray').checked;

    allData.forEach(record => {
        const status = getRecordStatus(record);
        if ((status === 'warning' && !showRed) ||
            (status === 'validated' && !showGreen) ||
            (status === 'empty' && !showGray)) return;

        tbody.appendChild(createTableRow(record, status));
    });
}

function createTableRow(record, status) {
    const tr = document.createElement('tr');

    // Pełna struktura kolumn: ID, ROK, Nr., Nazwisko, Imię, Miejscowość, ImięO, NazwiskoO, wiekO, IM, NM, wM, uwagi, UWAGI ORG, Akcje
    // UWAGI ORG - cała oryginalna linia TSV z | jako separator (dla parsera)
    const originalLine = [
        record.id,
        record.year || '',
        record.number || '',
        record.surname || '',
        record.name || '',
        record.place || '',
        record.fatherName || '',
        record.fatherSurname || '',
        record.fatherAge || '',
        record.motherName || '',
        record.motherSurname || '',
        record.motherAge || '',
        record.notes || ''
    ].join('|');
    
    const cells = [
        record.id,
        record.year || '-',
        record.number || '-',
        record.surname || '-',
        record.name || '-',
        record.place || '-',
        record.fatherName || '-',
        record.fatherSurname || '-',
        record.fatherAge || '-',
        record.motherName || '-',
        record.motherSurname || '-',
        record.motherAge || '-',
        record.notes || '-',
        originalLine,  // Pełny oryginalny wiersz z |
        `<button class="btn btn-small" onclick="openEditModal('${record.id}')">
            <span class="material-icons" style="font-size: 16px;">edit</span>
        </button>`
    ];

    cells.forEach((content, i) => {
        const td = document.createElement('td');
        
        // Kolumna ID sticky
        if (i === 0) {
            td.classList.add('sticky-col');
        }
        
        if (i === 14) {
            // Przycisk edit (ostatnia kolumna - indeks 14)
            td.innerHTML = content;
        } else {
            td.textContent = content;
            
            // CZERWONE/ZIELONE PODŚWIETLENIE dla wartości w bazie
            if (i === 3) {  // Nazwisko dziecka
                if (!record.surname || record.surname === '-') {
                    td.classList.add('text-empty');
                } else if (nameDatabase.allSurnames && nameDatabase.allSurnames.has(record.surname.toLowerCase())) {
                    td.classList.add('text-validated');
                    console.log('✅ Nazwisko dziecka w bazie:', record.surname);
                } else {
                    td.classList.add('cell-not-found');
                    console.log('❌ Nazwisko dziecka BRAK:', record.surname);
                }
            } else if (i === 4) {  // Imię dziecka
                if (!record.name || record.name === '-') {
                    td.classList.add('text-empty');
                } else if (nameDatabase.allNames && nameDatabase.allNames.has(record.name.toLowerCase())) {
                    td.classList.add('text-validated');
                    console.log('✅ Imię dziecka w bazie:', record.name);
                } else {
                    td.classList.add('cell-not-found');
                    console.log('❌ Imię dziecka BRAK:', record.name);
                }
            } else if (i === 6) {  // ImięO (Father Name)
                if (!record.fatherName || record.fatherName === '-') {
                    td.classList.add('text-empty');
                } else if (nameDatabase.allNames && nameDatabase.allNames.has(record.fatherName.toLowerCase())) {
                    td.classList.add('text-validated');
                } else {
                    td.classList.add('cell-not-found');
                }
            } else if (i === 7) {  // NazwiskoO (Father Surname)
                if (!record.fatherSurname || record.fatherSurname === '-') {
                    td.classList.add('text-empty');
                } else if (nameDatabase.allSurnames && nameDatabase.allSurnames.has(record.fatherSurname.toLowerCase())) {
                    td.classList.add('text-validated');
                } else {
                    td.classList.add('cell-not-found');
                }
            } else if (i === 9) {  // IM (Mother Name)
                if (!record.motherName || record.motherName === '-') {
                    td.classList.add('text-empty');
                } else if (nameDatabase.allNames && nameDatabase.allNames.has(record.motherName.toLowerCase())) {
                    td.classList.add('text-validated');
                } else {
                    td.classList.add('cell-not-found');
                }
            } else if (i === 10) {  // NM (Mother Surname)
                if (!record.motherSurname || record.motherSurname === '-') {
                    td.classList.add('text-empty');
                } else if (nameDatabase.allSurnames && nameDatabase.allSurnames.has(record.motherSurname.toLowerCase())) {
                    td.classList.add('text-validated');
                } else {
                    td.classList.add('cell-not-found');
                }
            }
            
            // Edytowalne pola - nowe indeksy dla 15 kolumn
            const editableFields = {
                6: 'fatherName',
                7: 'fatherSurname',
                8: 'fatherAge',
                9: 'motherName',
                10: 'motherSurname',
                11: 'motherAge'
            };
            
            if (editableFields[i]) {
                td.classList.add('cell-editable');
                td.onclick = () => openEditModal(record.id);
            }
        }
        
        tr.appendChild(td);
    });

    // Dodaj kliknięcie na wiersz aby pokazać oryginalną linię
    tr.style.cursor = 'pointer';
    tr.addEventListener('click', (e) => {
        // Nie reaguj jeśli kliknięto przycisk edycji
        if (e.target.closest('button')) return;
        showOriginalLine(record);
    });
    
    // Dodaj podwójne kliknięcie dla otwarcia modala
    tr.addEventListener('dblclick', (e) => {
        // Nie reaguj jeśli kliknięto przycisk
        if (e.target.closest('button')) return;
        openEditModal(record.id);
    });

    return tr;
}

function updateStats() {
    const total = allData.length;
    const validated = allData.filter(r => getRecordStatus(r) === 'validated').length;
    const warning = allData.filter(r => getRecordStatus(r) === 'warning').length;

    const recordCount = document.getElementById('recordCount');
    const confirmedCount = document.getElementById('confirmedCount');
    const warningCount = document.getElementById('warningCount');
    const progressPercent = document.getElementById('progressPercent');
    
    if (recordCount) recordCount.textContent = total;
    if (confirmedCount) confirmedCount.textContent = validated;
    if (warningCount) warningCount.textContent = warning;
    if (progressPercent) progressPercent.textContent = total > 0 ? Math.round(validated / total * 100) + '%' : '0%';
}

// ==================== WYŚWIETLANIE ORYGINALNEJ LINII ====================
function showOriginalLine(record) {
    const displayDiv = document.getElementById('originalLineDisplay');
    const recordIdSpan = document.getElementById('displayedRecordId');
    const contentDiv = document.getElementById('originalLineContent');
    
    if (!displayDiv || !contentDiv) return;
    
    // Pokaż okienko
    displayDiv.style.display = 'block';
    
    // Ustaw ID rekordu
    if (recordIdSpan) {
        recordIdSpan.textContent = record.id || '';
    }
    
    // Ustaw oryginalną linię
    // Jeśli jest pole 'original', użyj go; w przeciwnym razie zbuduj z pól
    let originalLine = record.original;
    if (!originalLine || originalLine.trim() === '') {
        // Zbuduj linię z dostępnych pól
        originalLine = [
            record.id,
            record.year,
            record.number,
            record.surname,
            record.name,
            record.place,
            record.fatherName,
            record.fatherSurname,
            record.fatherAge,
            record.motherName,
            record.motherSurname,
            record.motherAge,
            record.notes,
            record.originalNotes || ''
        ].join('\t');
    }
    
    // Ustaw tekst bez dodatkowych białych znaków
    contentDiv.textContent = originalLine.replace(/^\s+|\s+$/g, '');
}

// ==================== MODAL EDYCJI ====================
function openEditModal(id) {
    const record = allData.find(r => r.id === id);
    if (!record) {
        showNotification('Nie znaleziono rekordu', 'warning');
        return;
    }
    
    currentEditingRecord = record;

    // Wyświetl oryginalny tekst
    const originalTextDisplay = document.getElementById('originalTextDisplay');
    if (originalTextDisplay) {
        originalTextDisplay.textContent = record.original || '';
    }

    // Wypełnij dane dziecka
    document.getElementById('editID').value = record.id || '';
    document.getElementById('editYear').value = record.year || '';
    document.getElementById('editNumber').value = record.number || '';
    document.getElementById('editPlace').value = record.place || '';
    
    // Dziecko - surname
    const editSurname = document.getElementById('editSurname');
    editSurname.value = record.surname || '';
    updateFieldValidation(editSurname, record.surname, 'surname');
    showHintSource('hintChildSurname', record.surname || '');
    
    // Dziecko - name
    const editName = document.getElementById('editName');
    editName.value = record.name || '';
    updateFieldValidation(editName, record.name, 'name');
    showHintSource('hintChildName', record.name || '');

    // Ojciec - name
    const editFatherName = document.getElementById('editFatherName');
    editFatherName.value = record.fatherName || '';
    updateFieldValidation(editFatherName, record.fatherName, 'fatherName');
    showHintSource('hintFatherName', record.fatherName || '');
    
    // Ojciec - surname (inteligentna logika)
    let fatherSurname = record.fatherSurname || '';
    if (record.fatherName && !fatherSurname) {
        if (record.fatherName !== record.motherName) {
            fatherSurname = record.surname;
        }
    }
    const editFatherSurname = document.getElementById('editFatherSurname');
    editFatherSurname.value = fatherSurname;
    updateFieldValidation(editFatherSurname, fatherSurname, 'fatherSurname');
    showHintSource('hintFatherSurname', record.fatherSurname || '');
    
    // Ojciec - age
    document.getElementById('editFatherAge').value = record.fatherAge || '';

    // Matka - name
    const editMotherName = document.getElementById('editMotherName');
    editMotherName.value = record.motherName || '';
    updateFieldValidation(editMotherName, record.motherName, 'motherName');
    showHintSource('hintMotherName', record.motherName || '');
    
    // Matka - surname
    const editMotherSurname = document.getElementById('editMotherSurname');
    editMotherSurname.value = record.motherSurname || '';
    updateFieldValidation(editMotherSurname, record.motherSurname, 'motherSurname');
    showHintSource('hintMotherSurname', record.motherSurname || '');
    
    // Matka - age
    document.getElementById('editMotherAge').value = record.motherAge || '';

    // Uwagi
    document.getElementById('editNotes').value = record.notes || '';
    document.getElementById('editOriginalNotes').value = record.original || '';
    
    // Pokaż modal
    document.getElementById('modalRecordId').textContent = id;
    const editModal = document.getElementById('editModal');
    if (editModal) {
        // Użyj requestAnimationFrame dla płynniejszego wyświetlenia
        requestAnimationFrame(() => {
            editModal.style.display = 'flex';
        });
    }
}

// Zaktualizuj kolorowanie tekstu na podstawie walidacji
function updateFieldValidation(input, value, fieldType) {
    input.classList.remove('text-valid', 'text-invalid');
    
    if (!value) return; // Puste - bez koloru
    
    // Sprawdź walidację zależnie od typu pola
    let isValid = false;
    const normalizedValue = value.trim().toLowerCase();
    
    if (fieldType.includes('Surname')) {
        isValid = nameDatabase.allSurnames && nameDatabase.allSurnames.has(normalizedValue);
    } else if (fieldType.includes('Name') || fieldType === 'name') {
        isValid = nameDatabase.allNames && nameDatabase.allNames.has(normalizedValue);
    }
    
    if (isValid) {
        input.classList.add('text-valid');
    } else if (value.trim().length > 0) {
        input.classList.add('text-invalid');
    }
}

// Pokaż hint - fragment z oryginalnych danych
function showHintSource(elementId, originalValue) {
    const hint = document.getElementById(elementId);
    if (!hint) return;
    
    if (originalValue && originalValue.trim()) {
        hint.textContent = `z: "${originalValue.substring(0, 30)}${originalValue.length > 30 ? '...' : ''}"`;
    } else {
        hint.textContent = '';
    }
}

function closeEditModal() {
    const modal = document.getElementById('editModal');
    if (modal) modal.style.display = 'none';
    currentEditingRecord = null;
}

// ==================== KAFELKI DANYCH - DRAG & DROP (USUNIĘTE) ====================
// Stare funkcje displayOriginalLine, renderDataTiles, initializeDropZones, populateIDSelects zostały zastąpione przez Token Mapper

function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return (text || '').replace(/[&<>"']/g, m => map[m]);
}

function handleFormSubmit(e) {
    e.preventDefault();
    if (!currentEditingRecord) return;

    // Zapisz wszystkie dane dziecka
    currentEditingRecord.year = document.getElementById('editYear').value.trim();
    currentEditingRecord.number = document.getElementById('editNumber').value.trim();
    currentEditingRecord.surname = document.getElementById('editSurname').value.trim();
    currentEditingRecord.name = document.getElementById('editName').value.trim();
    currentEditingRecord.place = document.getElementById('editPlace').value.trim();

    // Zapisz dane rodziców
    currentEditingRecord.fatherName = document.getElementById('editFatherName').value.trim();
    currentEditingRecord.fatherSurname = document.getElementById('editFatherSurname').value.trim();
    currentEditingRecord.fatherAge = document.getElementById('editFatherAge').value.trim();
    currentEditingRecord.motherName = document.getElementById('editMotherName').value.trim();
    currentEditingRecord.motherSurname = document.getElementById('editMotherSurname').value.trim();
    currentEditingRecord.motherAge = document.getElementById('editMotherAge').value.trim();
    currentEditingRecord.motherMaidenName = document.getElementById('editMotherSurname').value.trim();
    currentEditingRecord.notes = document.getElementById('editNotes').value.trim();

    validateRecord(currentEditingRecord);
    generateTableWithBackend();
    updateStats();
    closeEditModal();
    
    showNotification('Zmiany zapisane', 'success');
}

// ==================== EKSPORT I ZAPIS ====================
function exportData() {
    if (allData.length === 0) {
        showNotification('Brak danych do eksportu', 'warning');
        return;
    }

    showNotification('Eksportowanie przez backend...', 'info');

    // Przygotuj dane w formacie oczekiwanym przez backend
    const records = allData.map(r => ({
        record_id: r.id,
        year: r.year,
        number: r.number,
        surname: r.surname,
        name: r.name,
        place: r.place,
        father_name: r.fatherName,
        father_surname: r.fatherSurname,
        father_age: r.fatherAge,
        mother_name: r.motherName,
        mother_surname: r.motherSurname,
        mother_age: r.motherAge,
        notes: r.notes,
        original: r.original
    }));

    fetch('http://127.0.0.1:5000/api/export/tsv', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            records: records
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`Błąd HTTP: ${response.status}`);
        }
        return response.blob();
    })
    .then(blob => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `rodzice-${new Date().toISOString().slice(0,10)}.tsv`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        
        showNotification(`Wyeksportowano ${allData.length} rekordów`, 'success');
    })
    .catch(error => {
        console.error('Błąd eksportu przez backend:', error);
        showNotification(`Błąd eksportu: ${error.message}`, 'error');
        
        // Fallback: lokalny eksport
        console.log('Próbuję lokalny eksport...');
        exportDataLocal();
    });
}

function exportDataLocal() {
    const headers = ['ID', 'ROK', 'Nr', 'Nazwisko', 'Imię', 'Miejscowość', 'ImięO', 'NazwiskoO', 'wiekO', 'IM', 'NM', 'wM', 'uwagi', 'UWAGI ORG'];
    const rows = allData.map(r => [
        r.id,
        r.year,
        r.number,
        r.surname,
        r.name,
        r.place,
        r.fatherName,
        r.fatherSurname,
        r.fatherAge,
        r.motherName,
        r.motherSurname,
        r.motherAge,
        r.notes,
        r.original
    ]);

    let tsv = headers.join('\t') + '\n';
    rows.forEach(row => {
        tsv += row.map(cell => `"${(cell || '').replace(/"/g, '""')}"`).join('\t') + '\n';
    });

    const blob = new Blob([tsv], { type: 'text/tab-separated-values;charset=utf-8' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `rodzice-${new Date().toISOString().slice(0,10)}.tsv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    
    showNotification(`Wyeksportowano ${allData.length} rekordów (lokalnie)`, 'success');
}

function saveToLocalStorage() {
    if (allData.length === 0) {
        showNotification('Brak danych do zapisania', 'warning');
        return;
    }
    
    localStorage.setItem('agene_parent_data', JSON.stringify(allData));
    showNotification(`Zapisano ${allData.length} rekordów w przeglądarce`, 'success');
}

function clearAllData() {
    if (confirm('Czy na pewno chcesz wyczyścić WSZYSTKIE dane?\n\nTo usunie:\n- Dane w pamięci (aktualnie wyświetlone)\n- Dane zapisane w przeglądarce (localStorage)\n\nTej operacji nie można cofnąć!')) {
        // Wyczyść dane w pamięci
        allData = [];
        
        // Wyczyść localStorage
        localStorage.removeItem('agene_parent_data');
        
        // Wyczyść interfejs
        const tbody = document.getElementById('tableBody');
        if (tbody) tbody.innerHTML = '';
        
        const statsPanel = document.getElementById('statsPanel');
        if (statsPanel) statsPanel.style.display = 'none';
        
        showNotification('Wszystkie dane zostały wyczyszczone', 'success');
    }
}

// ==================== NOTYFIKACJE ====================
function showNotification(message, type = 'info') {
    // Usuń istniejące notyfikacje
    document.querySelectorAll('.notification').forEach(n => n.remove());
    
    const el = document.createElement('div');
    el.className = 'notification';
    el.textContent = message;
    
    const colors = {
        success: '#27ae60',
        warning: '#e67e22',
        info: '#3498db',
        error: '#e74c3c'
    };
    
    el.style.cssText = `
        position: fixed; top: 20px; right: 20px; z-index: 9999;
        padding: 12px 24px; border-radius: 6px; color: white;
        background: ${colors[type] || colors.info};
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        animation: slideIn 0.3s ease;
        font-family: 'Roboto', sans-serif;
        font-weight: 500;
    `;
    
    document.body.appendChild(el);

    setTimeout(() => {
        el.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => el.remove(), 300);
    }, 4000);
}

// ==================== MODAL - MAPOWANIE KOLUMN ID ====================
function showColumnMappingModal(dataLines, separator) {
    if (dataLines.length === 0) {
        showNotification('Brak danych do przetworzenia', 'error');
        return;
    }
    
    const firstLine = dataLines[0].split(separator);
    const columns = firstLine.map((col, idx) => ({
        index: idx,
        preview: col.substring(0, 30),
        count: dataLines.filter(line => line.split(separator)[idx]?.trim()).length
    }));
    
    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.innerHTML = `
        <div class="modal-dialog modal-large">
            <div class="modal-header">
                <h3>Gdzie znajduje się ID?</h3>
                <p style="font-size: 0.85em; color: #aaa; margin: 4px 0 0 0;">Wybierz kolumnę zawierającą ID rekordów (lub będą autogenerowane)</p>
            </div>
            <div class="modal-body" style="max-height: 400px; overflow-y: auto;">
                <div class="column-selector">
                    ${columns.map(col => `
                        <div class="column-option" onclick="selectIdColumn(${col.index}, '${separator}', ${JSON.stringify(dataLines)})">
                            <div class="col-number">Kolumna ${col.index}</div>
                            <div class="col-preview">${col.preview}</div>
                            <div class="col-stats">${col.count}/${dataLines.length} wartości</div>
                        </div>
                    `).join('')}
                    <div class="column-option autogen" onclick="selectIdColumn(-1, '${separator}', ${JSON.stringify(dataLines)})">
                        <div class="col-number">🤖 Autogeneruj</div>
                        <div class="col-preview">ID będą tworzone automatycznie z imienia rodzica</div>
                        <div class="col-stats">Rekomendowane</div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    modal.style.display = 'flex';
}

function selectIdColumn(colIndex, separator, dataLines) {
    const modal = document.querySelector('.modal-overlay');
    if (modal) modal.remove();
    
    allData = [];
    
    dataLines.forEach((line, index) => {
        const fields = line.split(separator).map(f => f.trim());
        
        let record;
        const fieldCount = fields.length;
        
        if (fieldCount >= 13) {
            record = {
                id: colIndex === -1 ? '' : (fields[colIndex] || ''),
                surname: fields[1] || '',
                name: fields[2] || '',
                year: fields[3] || '',
                place: fields[4] || '',
                fatherName: fields[5] || '',
                fatherSurname: fields[7] || '',
                motherName: fields[8] || '',
                motherSurname: fields[10] || '',
                motherMaidenName: fields[10] || '',
                notes: fields[11] || '',
                original: line,
                fatherNameValidated: false,
                fatherSurnameValidated: false,
                motherNameValidated: false,
                motherSurnameValidated: false,
                motherMaidenNameValidated: false
            };
        } else if (fieldCount >= 8) {
            record = {
                id: colIndex === -1 ? '' : (fields[colIndex] || ''),
                surname: fields[1] || '',
                name: fields[2] || '',
                year: fields[3] || '',
                place: '',
                fatherName: fields[4] || '',
                fatherSurname: fields[5] || '',
                motherName: fields[6] || '',
                motherSurname: fields[7] || '',
                motherMaidenName: fields[7] || '',
                notes: '',
                original: line,
                fatherNameValidated: false,
                fatherSurnameValidated: false,
                motherNameValidated: false,
                motherSurnameValidated: false,
                motherMaidenNameValidated: false
            };
        } else {
            record = {
                id: colIndex === -1 ? '' : (fields[colIndex] || ''),
                surname: fields[1] || '',
                name: fields[2] || '',
                year: '',
                place: '',
                fatherName: '',
                fatherSurname: '',
                motherName: '',
                motherSurname: '',
                motherMaidenName: '',
                notes: '',
                original: line,
                fatherNameValidated: false,
                fatherSurnameValidated: false,
                motherNameValidated: false,
                motherSurnameValidated: false,
                motherMaidenNameValidated: false
            };
        }
        
        if (!record.id || record.id === '') {
            record.id = generateAutoId(record, index);
        }
        
        validateRecord(record);
        allData.push(record);
    });
    
    displayData();
    showNotification(`Załadowano ${allData.length} rekordów (ID z kolumny ${colIndex === -1 ? 'autogenerowane' : colIndex})`, 'success');
}

function generateAutoId(record, index = 0) {
    // Generuj ID z rodzica, roku, imienia
    const parent = (record.motherName || record.fatherName || 'REC').substring(0, 3).toUpperCase();
    const year = record.year ? record.year.toString().slice(-2) : 'XX';
    const child = (record.name || 'X').substring(0, 2).toUpperCase();
    const num = String(index + 1).padStart(4, '0');
    return `${parent}.${year}.${child}.${num}`;
}

// Dodaj style dla animacji notyfikacji
if (!document.querySelector('#notification-styles')) {
    const style = document.createElement('style');
    style.id = 'notification-styles';
    style.textContent = `
        @keyframes slideIn { from { transform: translateX(100%); opacity: 0; } to { transform: translateX(0); opacity: 1; } }
        @keyframes slideOut { from { transform: translateX(0); opacity: 1; } to { transform: translateX(100%); opacity: 0; } }
        
        .row-warning { background-color: #fff5f5 !important; }
        .row-validated { background-color: #f0fff4 !important; }
        .row-empty { background-color: #f7fafc !important; }
    `;
    document.head.appendChild(style);
}

// ==================== FUNKCJA POMOCY ====================
function showFormatHelp() {
    const modal = document.getElementById('helpModal');
    if (modal) {
        modal.style.display = 'flex';
    } else {
        showNotification('Format pomocy: Wklej dane TSV (tab-separated) z Excela lub pliku tekstowego', 'info');
    }
}

// ==================== TOGGLE PANELS ====================
let panelsHidden = false;

function togglePanels() {
    const controlPanel = document.querySelector('.control-panel');
    const bottomPanel = document.getElementById('bottomPanel');
    const icon = document.getElementById('togglePanelsIcon');
    
    panelsHidden = !panelsHidden;
    
    if (panelsHidden) {
        // Ukryj panele
        document.body.classList.add('panels-hidden');
        if (controlPanel) controlPanel.style.display = 'none';
        if (bottomPanel) bottomPanel.style.display = 'none';
        if (icon) icon.textContent = 'unfold_more';
    } else {
        // Pokaż panele
        document.body.classList.remove('panels-hidden');
        if (controlPanel) controlPanel.style.display = 'block';
        if (bottomPanel) bottomPanel.style.display = 'block';
        if (icon) icon.textContent = 'unfold_less';
    }
}

