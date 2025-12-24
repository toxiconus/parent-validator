# Parent Validator - AI Coding Guidelines

## Project Overview
Genealogical data validator for Polish baptism, death, and marriage records (1783-1900). Web app with HTML/JS frontend and Python Flask backend. Handles parsing 5 data formats, validation against name databases, and record editing with support for multiple record types.

## Architecture
- **Frontend**: `index.html` + `parent-validator.js` + `parent-validator.css` - Data table, editing modal, file upload
- **Backend**: `backend.py` (Flask API) + `parser_v2.py` - Parsing, validation, export
- **Data Flow**: TSV input → Parser → Validation → Color-coded table → Edit modal → TSV/JSON export

## Key Conventions
- **Language**: Polish UI/comments, English code structure
- **Color Coding**: 🟢 Green (validated), 🔴 Red (check needed), ⚪ Gray (missing)
- **Age Format**: "l.40" (lat 40), birth estimate "~ 1801"
- **Record Types**: baptism (chrzest), death (zgon), marriage (małżeństwo)
- **File Structure**: Keep HTML/JS/CSS separate, backend modular

## Development Workflow
- Start: `.\start-all-local.bat` (frontend localhost:8080, backend :5000)
- Test data: "Załaduj z parsera" loads 5947 baptism records
- Edit: Double-click table row opens modal in `edit-modal.html`
- Export: `/api/export/tsv` endpoint

## Common Patterns
- **Validation**: Check against `nameDatabase` (male/female names/surnames from JSON files)
- **Parsing**: Handle 5 formats (A-E) in `parser_v2.py`, preserve special markers (?, x, ..)
- **Modal**: Load `edit-modal.html` dynamically, populate with record data, toggle sections by record type
- **API Calls**: Use fetch() to `/api/parse`, `/api/validate`, `/api/table`
- **Record Types**: Use `recordType` field to control visible sections in modal

## Dependencies
- Backend: flask, flask-cors
- Frontend: Vanilla JS, Material Icons, no frameworks
- Data: ../../../data/imiona_*.json, nazwiska_*.json

## File Examples
- **Record Structure**: `{id: "CH.LUB.BLIN.0001574", surname: "Zyśko", name: "Zofia", recordType: "baptism", fatherName: "Józef", fatherSurname: "Zyśko", fatherAge: "l.40"}`
- **API Response**: JSON with status, data array, validation flags
- **Table Row**: `<tr class="status-green">` with onclick="openEditModal(record)"
