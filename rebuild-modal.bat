@echo off
echo Tworzenie nowego edit-modal.html...
cd /d J:\A.Gene\modules\data-entry\parent-validator
del edit-modal.html
echo ^<!-- Modal edycji rekordu - Full Screen Redesign --^> > edit-modal.html
echo ^<div class="modal-overlay" id="editModal"^> >> edit-modal.html
echo     ^<div class="modal-content modal-fullscreen"^> >> edit-modal.html
echo         ^<div class="modal-header"^> >> edit-modal.html
echo             ^<h2^>Edycja rekordu ^<span id="modalRecordId"^>^</span^>^</h2^> >> edit-modal.html
echo             ^<button class="close-btn" onclick="closeEditModal()"^>×^</button^> >> edit-modal.html
echo         ^</div^> >> edit-modal.html
echo         ^<div class="modal-body"^> >> edit-modal.html
echo             ^<!-- Oryginalny tekst - sticky --^> >> edit-modal.html
echo             ^<div class="original-text-section"^> >> edit-modal.html
echo                 ^<div class="section-header"^> >> edit-modal.html
echo                     ^<span class="material-icons"^>description^</span^> >> edit-modal.html
echo                     ^<span^>ORYGINALNY TEKST (TSV z ^| separatorami)^</span^> >> edit-modal.html
echo                 ^</div^> >> edit-modal.html
echo                 ^<div class="original-text-display" id="originalTextDisplay"^>^</div^> >> edit-modal.html
echo             ^</div^> >> edit-modal.html
echo             ^<form id="editForm"^> >> edit-modal.html
echo                 ^<!-- Gorny pasek - najwazniejsze dane --^> >> edit-modal.html
echo                 ^<div class="top-bar"^> >> edit-modal.html
echo                     ^<div class="top-bar-item"^> >> edit-modal.html
echo                         ^<label^>ROK^</label^> >> edit-modal.html
echo                         ^<input type="text" id="editYear"^> >> edit-modal.html
echo                     ^</div^> >> edit-modal.html
echo                     ^<div class="top-bar-item"^> >> edit-modal.html
echo                         ^<label^>Miejscowosc^</label^> >> edit-modal.html
echo                         ^<input type="text" id="editPlace"^> >> edit-modal.html
echo                     ^</div^> >> edit-modal.html
echo                     ^<div class="top-bar-item"^> >> edit-modal.html
echo                         ^<label^>Nr aktu^</label^> >> edit-modal.html
echo                         ^<input type="text" id="editNumber"^> >> edit-modal.html
echo                     ^</div^> >> edit-modal.html
echo                     ^<div class="top-bar-item"^> >> edit-modal.html
echo                         ^<label^>ID (readonly)^</label^> >> edit-modal.html
echo                         ^<input type="text" id="editID" readonly^> >> edit-modal.html
echo                     ^</div^> >> edit-modal.html
echo                 ^</div^> >> edit-modal.html
echo                 ^<!-- Dane dziecka - kompaktowe --^> >> edit-modal.html
echo                 ^<div class="form-section compact"^> >> edit-modal.html
echo                     ^<div class="section-title"^>📋 Dziecko^</div^> >> edit-modal.html
echo                     ^<div class="form-row compact-row"^> >> edit-modal.html
echo                         ^<div class="form-group"^> >> edit-modal.html
echo                             ^<label^>Nazwisko ^<span class="validation-indicator" id="validChildSurname"^>^</span^>^</label^> >> edit-modal.html
echo                             ^<input type="text" id="editSurname"^> >> edit-modal.html
echo                         ^</div^> >> edit-modal.html
echo                         ^<div class="form-group"^> >> edit-modal.html
echo                             ^<label^>Imie ^<span class="validation-indicator" id="validChildName"^>^</span^>^</label^> >> edit-modal.html
echo                             ^<input type="text" id="editName"^> >> edit-modal.html
echo                         ^</div^> >> edit-modal.html
echo                     ^</div^> >> edit-modal.html
echo                 ^</div^> >> edit-modal.html
echo                 ^<!-- Rodzice obok siebie --^> >> edit-modal.html
echo                 ^<div class="parents-container"^> >> edit-modal.html
echo                     ^<!-- Ojciec po lewej --^> >> edit-modal.html
echo                     ^<div class="parent-section parent-left"^> >> edit-modal.html
echo                         ^<h3 class="parent-title"^>👨 Ojciec^</h3^> >> edit-modal.html
echo                         ^<div class="form-group"^> >> edit-modal.html
echo                             ^<label^>Imie ^<span class="validation-indicator" id="validFatherName"^>^</span^>^</label^> >> edit-modal.html
echo                             ^<input type="text" id="editFatherName" placeholder="np. Jozef"^> >> edit-modal.html
echo                         ^</div^> >> edit-modal.html
echo                         ^<div class="form-group"^> >> edit-modal.html
echo                             ^<label^>Nazwisko ^<span class="validation-indicator" id="validFatherSurname"^>^</span^>^</label^> >> edit-modal.html
echo                             ^<input type="text" id="editFatherSurname" placeholder="np. Kowalski"^> >> edit-modal.html
echo                         ^</div^> >> edit-modal.html
echo                         ^<div class="form-group"^> >> edit-modal.html
echo                             ^<label^>Wiek^</label^> >> edit-modal.html
echo                             ^<input type="text" id="editFatherAge" placeholder="np. 35"^> >> edit-modal.html
echo                         ^</div^> >> edit-modal.html
echo                     ^</div^> >> edit-modal.html
echo                     ^<!-- Matka po prawej --^> >> edit-modal.html
echo                     ^<div class="parent-section parent-right"^> >> edit-modal.html
echo                         ^<h3 class="parent-title"^>👩 Matka^</h3^> >> edit-modal.html
echo                         ^<div class="form-group"^> >> edit-modal.html
echo                             ^<label^>Imie ^<span class="validation-indicator" id="validMotherName"^>^</span^>^</label^> >> edit-modal.html
echo                             ^<input type="text" id="editMotherName" placeholder="np. Anna"^> >> edit-modal.html
echo                         ^</div^> >> edit-modal.html
echo                         ^<div class="form-group"^> >> edit-modal.html
echo                             ^<label^>Nazwisko panienskie ^<span class="validation-indicator" id="validMotherSurname"^>^</span^>^</label^> >> edit-modal.html
echo                             ^<input type="text" id="editMotherSurname" placeholder="np. Nowak"^> >> edit-modal.html
echo                         ^</div^> >> edit-modal.html
echo                         ^<div class="form-group"^> >> edit-modal.html
echo                             ^<label^>Wiek^</label^> >> edit-modal.html
echo                             ^<input type="text" id="editMotherAge" placeholder="np. 30"^> >> edit-modal.html
echo                         ^</div^> >> edit-modal.html
echo                     ^</div^> >> edit-modal.html
echo                 ^</div^> >> edit-modal.html
echo                 ^<!-- Uwagi --^> >> edit-modal.html
echo                 ^<div class="form-section notes-section"^> >> edit-modal.html
echo                     ^<div class="form-row"^> >> edit-modal.html
echo                         ^<div class="form-group full-width"^> >> edit-modal.html
echo                             ^<label^>Uwagi^</label^> >> edit-modal.html
echo                             ^<textarea id="editNotes" rows="2" placeholder="Dodatkowe informacje..."^>^</textarea^> >> edit-modal.html
echo                         ^</div^> >> edit-modal.html
echo                     ^</div^> >> edit-modal.html
echo                     ^<div class="form-row"^> >> edit-modal.html
echo                         ^<div class="form-group full-width"^> >> edit-modal.html
echo                             ^<label^>UWAGI ORG (read-only - pelna linia TSV)^</label^> >> edit-modal.html
echo                             ^<textarea id="editOriginalNotes" rows="2" readonly placeholder="Oryginalne dane (tylko do odczytu)"^>^</textarea^> >> edit-modal.html
echo                         ^</div^> >> edit-modal.html
echo                     ^</div^> >> edit-modal.html
echo                 ^</div^> >> edit-modal.html
echo                 ^<!-- Przyciski akcji --^> >> edit-modal.html
echo                 ^<div class="form-actions"^> >> edit-modal.html
echo                     ^<button type="submit" class="btn btn-primary"^> >> edit-modal.html
echo                         ^<span class="material-icons"^>save^</span^> Zapisz zmiany >> edit-modal.html
echo                     ^</button^> >> edit-modal.html
echo                     ^<button type="button" class="btn btn-secondary" onclick="closeEditModal()"^> >> edit-modal.html
echo                         ^<span class="material-icons"^>close^</span^> Anuluj >> edit-modal.html
echo                     ^</button^> >> edit-modal.html
echo                 ^</div^> >> edit-modal.html
echo             ^</form^> >> edit-modal.html
echo         ^</div^> >> edit-modal.html
echo     ^</div^> >> edit-modal.html
echo ^</div^> >> edit-modal.html
echo OK - plik utworzony!
