#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flask backend dla Parent Validator UI
Obsługuje parsowanie i walidację danych genealogicznych
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import json
import os
from datetime import datetime
from parser_v2 import ParentParser, ParsingStatus
import io
import re

app = Flask(__name__)
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:8000", "http://127.0.0.1:8000", "http://localhost:8080", "http://127.0.0.1:8080", "http://localhost:5000", "http://10.42.163.151:8080", "http://10.42.163.151:5000"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        response = jsonify({'status': 'ok'})
        return response, 200

@app.after_request
def after_request(response):
    # CORS już obsługuje nagłówki, nie dodawaj ręcznie
    return response

# Configuration
DATA_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(DATA_DIR, 'uploads')
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Load name database for validation
NAME_DATABASE = {
    'male_names': set(),
    'female_names': set(),
    'all_names': set(),
    'male_surnames': set(),
    'female_surnames': set(),
    'all_surnames': set(),
    'places': set()
}

def load_name_databases():
    """Załaduj bazy imion, nazwisk i miejscowości"""
    global NAME_DATABASE
    
    data_files = {
        'male_names': 'data/imiona_meskie.json',
        'female_names': 'data/imiona_zenskie.json',
        'all_names': 'data/imiona_wszystkie.json',
        'male_surnames': 'data/nazwiska_meskie.json',
        'female_surnames': 'data/nazwiska_zenskie.json',
        'all_surnames': 'data/nazwiska_wszystkie.json'
    }
    
    for key, path in data_files.items():
        full_path = os.path.join(DATA_DIR, path)
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Convert to lowercase for case-insensitive matching
                if isinstance(data, list):
                    NAME_DATABASE[key] = set(name.lower() for name in data)
                else:
                    NAME_DATABASE[key] = set(key.lower() for key in data.keys())
                print(f"✓ Załadowano {len(NAME_DATABASE[key])} {key}")
        except Exception as e:
            print(f"⚠ Nie udało się załadować {key}: {e}")
    
    # Load places database
    places_path = os.path.join(DATA_DIR, 'data', 'places.json')
    try:
        with open(places_path, 'r', encoding='utf-8') as f:
            places_data = json.load(f)
            NAME_DATABASE['places'] = set(place.lower() for place in places_data)
            print(f"✓ Załadowano {len(NAME_DATABASE['places'])} miejscowości")
    except Exception as e:
        print(f"⚠ Nie udało się załadować places: {e}")
        NAME_DATABASE['places'] = set()

def parse_data_local(data_lines, separator='\t'):
    """
    Lokalny parser JavaScript-style gdy parser_v2.py nie działa
    Implementuje logikę z parseDataWithIds z JavaScript
    """
    records = []
    
    for index, line in enumerate(data_lines):
        fields = [f.strip() for f in line.split(separator)]
        
        # Pomiń puste linie
        if not any(fields):
            continue
        
        # Pomiń linię nagłówkową (jeśli pierwsza kolumna to "ID" i druga to "ROK" lub "Imię")
        if index == 0 and fields[0].upper() == 'ID':
            # Sprawdź czy to nagłówek (druga kolumna zawiera nazwę pola zamiast wartości)
            if len(fields) > 1 and (fields[1].upper() in ['ROK', 'IMIĘ', 'IMIE', 'NAZWISKO']):
                print(f"⚠ Pominięto linię nagłówkową: {line[:100]}")
                continue
            
        record_id = fields[0] if len(fields) > 0 else f'auto_{index}'
        field_count = len(fields)
        
        record = {
            'id': record_id,
            'year': '',
            'number': '',
            'surname': '',
            'name': '',
            'place': '',
            'fatherName': '',
            'fatherSurname': '',
            'fatherAge': '',
            'motherName': '',
            'motherSurname': '',
            'motherAge': '',
            'motherMaidenName': '',
            'notes': '',
            'original': line,
            'fatherNameValidated': False,
            'fatherSurnameValidated': False,
            'motherNameValidated': False,
            'motherSurnameValidated': False,
            'motherMaidenNameValidated': False
        }
        
        # Parsuj zależnie od liczby kolumn (jak w JavaScript)
        if field_count >= 12:
            # Sprawdź czy druga kolumna to rok (cyfry) czy nazwisko (tekst)
            is_new_format = len(fields) > 1 and fields[1].isdigit() and len(fields[1]) == 4
            
            if is_new_format:
                # Format "ur nowe blinow.txt": ID|ROK|Nr|Nazwisko|Imię|Miejscowość|ImięO|NazwiskoO|wiekO|IM|NM|wM|uwagi
                record.update({
                    'year': fields[1],
                    'number': fields[2],
                    'surname': fields[3],
                    'name': fields[4],
                    'place': fields[5],
                    'fatherName': fields[6],
                    'fatherSurname': fields[7],
                    'fatherAge': fields[8],
                    'motherName': fields[9],
                    'motherSurname': fields[10],
                    'motherAge': fields[11],
                    'motherMaidenName': fields[10],
                    'notes': fields[12] if len(fields) > 12 else ''
                })
            else:
                # Stary format rozszerzony
                record.update({
                    'surname': fields[1],
                    'name': fields[2],
                    'number': fields[3],
                    'year': fields[4],
                    'place': fields[6],
                    'fatherName': fields[7],
                    'fatherSurname': fields[8],
                    'fatherAge': fields[9],
                    'motherName': fields[11],
                    'motherSurname': fields[12],
                    'motherAge': fields[13],
                    'motherMaidenName': fields[12],
                    'notes': fields[14] if len(fields) > 14 else ''
                })
                
        elif field_count >= 8:
            # Stary format lub z genealogią
            genealogical_string = fields[7] if len(fields) > 7 else ''
            
            # Sprawdź czy zawiera dane genealogiczne
            has_genealogy = any(keyword in genealogical_string for keyword in [' i ', 's.', 'c.', ' z ', '/'])
            
            if has_genealogy:
                # Parsuj dane genealogiczne
                genealogy = parse_genealogical_data_local(genealogical_string)
                record.update({
                    'surname': fields[1],
                    'name': fields[2],
                    'year': fields[4] if len(fields) > 4 else '',
                    'place': genealogy.get('place', ''),
                    'fatherName': genealogy.get('fatherName', ''),
                    'fatherSurname': genealogy.get('fatherSurname', ''),
                    'motherName': genealogy.get('motherName', ''),
                    'motherSurname': genealogy.get('motherSurname', ''),
                    'motherMaidenName': genealogy.get('motherSurname', ''),
                    'notes': genealogical_string
                })
            else:
                # Standardowy stary format
                record.update({
                    'surname': fields[1],
                    'name': fields[2],
                    'year': fields[4] if len(fields) > 4 else '',
                    'place': fields[6] if len(fields) > 6 else '',
                    'notes': genealogical_string
                })
        else:
            # Krótki format - inteligentne rozpoznawanie
            year_value = ''
            number_value = ''
            surname_value = ''
            name_value = ''
            
            # Sprawdź ID typu CH.LUB.BLIN.1908.001
            id_match = re.match(r'.*\.(\d{4})\.(\d{1,3})$', record_id)
            if id_match and field_count <= 5:
                year_value = id_match.group(1)
                number_value = id_match.group(2).lstrip('0') or id_match.group(2)
            
            # Przeszukaj pola
            numeric_fields = []
            text_fields = []
            
            for idx, field in enumerate(fields):
                if idx == 0 and record_id:
                    continue
                if field.isdigit():
                    numeric_fields.append({'value': field, 'index': idx})
                elif field.strip():
                    text_fields.append({'value': field, 'index': idx})
            
            # Znajdź rok jeśli nie z ID
            if not year_value:
                for nf in numeric_fields:
                    num = int(nf['value'])
                    if len(nf['value']) == 4 and 1000 <= num <= 2500:
                        year_value = nf['value']
                        break
            
            # Znajdź numer aktu
            if not number_value:
                for nf in numeric_fields:
                    if nf['value'] != year_value and len(nf['value']) <= 3:
                        number_value = nf['value']
                        break
            
            # Pierwsze dwa pola tekstowe to nazwisko i imię
            surname_value = ''
            name_value = ''
            place_value = ''
            
            if text_fields:
                surname_value = text_fields[0]['value']
                if len(text_fields) > 1:
                    name_value = text_fields[1]['value']
                if len(text_fields) > 2:
                    place_value = text_fields[2]['value']  # Trzecie pole tekstowe jako miejsce
            
            record.update({
                'surname': surname_value,
                'name': name_value,
                'number': number_value,
                'year': year_value,
                'place': place_value  # Teraz miejsce jest ustawiane dla krótkich rekordów
            })
        
        # Generuj sformatowane uwagi ZAWSZE (rozszerz istniejące jeśli są)
        existing_notes = record.get('notes', '').strip()
        formatted_notes = build_formatted_notes(record)
        
        if formatted_notes:
            if existing_notes and existing_notes != '-':
                # Dodaj istniejące uwagi na końcu jeśli się różnią
                if existing_notes not in formatted_notes:
                    record['notes'] = f"{formatted_notes}. {existing_notes}"
                else:
                    record['notes'] = formatted_notes
            else:
                record['notes'] = formatted_notes
        
        # Walidacja rekordu
        validate_record_local(record)
        records.append(record)
    
    return records

def build_formatted_notes(record):
    """
    Buduje sformatowane uwagi w stylu: 
    "Miejscowość, O: ImięO NazwiskoO l.wiekO, M: IM NM l.wM"
    """
    parts = []
    
    # Miejscowość
    place = record.get('place', '').strip()
    if place and place != '-':
        parts.append(place)
    
    # Ojciec
    father_parts = []
    f_name = record.get('fatherName', '').strip()
    f_surname = record.get('fatherSurname', '').strip()
    f_age = record.get('fatherAge', '').strip()
    
    if f_name or f_surname:
        if f_name and f_name != '-':
            father_parts.append(f_name)
        if f_surname and f_surname != '-':
            father_parts.append(f_surname)
        if f_age and f_age != '-':
            father_parts.append(f'l.{f_age}' if not f_age.startswith('l.') else f_age)
        
        if father_parts:
            parts.append(f"O: {' '.join(father_parts)}")
    
    # Matka
    mother_parts = []
    m_name = record.get('motherName', '').strip()
    m_surname = record.get('motherSurname', '').strip()
    m_age = record.get('motherAge', '').strip()
    
    if m_name or m_surname:
        if m_name and m_name != '-':
            mother_parts.append(m_name)
        if m_surname and m_surname != '-':
            mother_parts.append(m_surname)
        if m_age and m_age != '-':
            mother_parts.append(f'l.{m_age}' if not m_age.startswith('l.') else m_age)
        
        if mother_parts:
            parts.append(f"M: {' '.join(mother_parts)}")
    
    return ', '.join(parts) if parts else ''

def parse_genealogical_data_local(text):
    """
    Parsuj dane genealogiczne z tekstu (jak w JavaScript)
    Wzorce: "Blinów / Tomasz l.45 i Antonina Pazdrak l.45"
            "Blinów s. Marcina i Katarzyny z Kurczaków"
    """
    result = {
        'place': '',
        'fatherName': '',
        'fatherSurname': '',
        'motherName': '',
        'motherSurname': ''
    }
    
    work_text = text.strip()
    
    # Wyciągnij miejscowość przed / lub - lub s. lub c.
    place_match = re.match(r'^([^\/\-]+?)\s*[\/\-]', work_text)
    if not place_match:
        place_match = re.match(r'^([^\s]+)\s+[sc]\.', work_text)
    
    if place_match:
        result['place'] = place_match.group(1).strip()
        work_text = work_text[place_match.end():].strip()
    
    # Znajdź separator " i "
    if ' i ' in work_text:
        parts = work_text.split(' i ', 1)
        
        # Ojciec (pierwsza część)
        father_text = parts[0].strip()
        # Usuń "s.", "c.", "l.XX"
        father_text = re.sub(r'^[sc]\.\s*', '', father_text)
        father_text = re.sub(r'\s+l\.\d+', '', father_text).strip()
        father_parts = father_text.split()
        if father_parts:
            result['fatherName'] = father_parts[0]
            if len(father_parts) > 1:
                # Wszystkie pozostałe części to nazwisko
                result['fatherSurname'] = ' '.join(father_parts[1:])
        
        # Matka (druga część)
        mother_text = parts[1].strip()
        # Usuń "l.XX" z końca
        mother_text = re.sub(r'\s+l\.\d+', '', mother_text).strip()
        
        # Sprawdź "z XYZ" (nazwisko panieńskie)
        maiden_match = re.search(r'\s+z\s+(.+?)(?:\.|$)', mother_text)
        if maiden_match:
            result['motherSurname'] = maiden_match.group(1).strip()
            # Usuń część "z XYZ" z tekstu
            mother_text = mother_text[:mother_text.index(' z ')].strip()
        
        mother_parts = mother_text.split()
        if mother_parts:
            result['motherName'] = mother_parts[0]
            # Jeśli nie ma nazwiska z "z XYZ" i jest więcej części
            if not result['motherSurname'] and len(mother_parts) > 1:
                result['motherSurname'] = ' '.join(mother_parts[1:])
    
    return result

def validate_record_local(record):
    """
    Walidacja rekordu względem baz danych (jak w JavaScript) - case insensitive
    """
    # Sprawdź imiona (case insensitive)
    father_name = record.get('fatherName', '').lower() if record.get('fatherName') else ''
    mother_name = record.get('motherName', '').lower() if record.get('motherName') else ''
    
    # Dla rodziców: TYLKO płciowe imiona (męskie dla ojca, żeńskie dla matki)
    record['fatherNameValidated'] = father_name in NAME_DATABASE['male_names'] if father_name else False
    record['motherNameValidated'] = mother_name in NAME_DATABASE['female_names'] if mother_name else False
    
    # Sprawdź nazwiska (case insensitive) - TYLKO płciowe dla rodziców
    father_surname = record.get('fatherSurname', '').lower() if record.get('fatherSurname') else ''
    mother_surname = record.get('motherSurname', '').lower() if record.get('motherSurname') else ''
    mother_maiden = record.get('motherMaidenName', '').lower() if record.get('motherMaidenName') else ''
    
    # Dla ojca TYLKO nazwiska męskie
    record['fatherSurnameValidated'] = father_surname in NAME_DATABASE['male_surnames'] if father_surname else False
    
    # Dla matki TYLKO nazwiska żeńskie
    record['motherSurnameValidated'] = mother_surname in NAME_DATABASE['female_surnames'] if mother_surname else False
    record['motherMaidenNameValidated'] = mother_maiden in NAME_DATABASE['female_surnames'] if mother_maiden else False
    
    # Sprawdź miejsce (case insensitive)
    place = record.get('place', '').lower() if record.get('place') else ''
    record['placeValidated'] = place in NAME_DATABASE['places'] if place else False
    
    # Sprawdź wiek rodziców
    record['fatherAgeValidated'] = validate_parent_age(record.get('fatherAge', ''))
    record['motherAgeValidated'] = validate_parent_age(record.get('motherAge', ''))

def validate_parent_age(age_str):
    """
    Walidacja wieku rodzica - sprawdź czy jest w rozsądnym przedziale
    """
    if not age_str or age_str.strip() == '' or age_str == '-':
        return None  # Brak danych - nie waliduj
    
    try:
        # Usuń "l." jeśli występuje
        age_clean = age_str.replace('l.', '').strip()
        age = int(age_clean)
        
        # Sprawdzone przedziały wiekowe dla rodziców w XIX wieku
        # Ojciec: 16-70 lat (minimalny wiek ojcostwa, maksymalny rozsądny wiek)
        # Matka: 14-50 lat (minimalny wiek macierzyństwa, maksymalny rozsądny wiek)
        # Będziemy używać tych samych granic dla obu rodziców dla uproszczenia
        
        if 14 <= age <= 70:
            return True
        else:
            return False
            
    except (ValueError, AttributeError):
        return False  # Niepoprawny format wieku

@app.route('/api/health', methods=['GET'])
def health():
    """Sprawdź status serwera"""
    return jsonify({
        'status': 'ok',
        'service': 'Parent Validator Backend',
        'version': '1.0',
        'loaded_names': {k: len(v) for k, v in NAME_DATABASE.items()}
    })

@app.route('/api/parse', methods=['POST'])
def parse_data():
    """
    Parsuj dane rodziców z pliku lub tekstu
    POST body: {
        'data': 'TSV data',  # lub
        'file': <file>,
        'format': 'tsv|csv'
    }
    """
    try:
        parser = ParentParser()
        
        # Check if file upload
        if 'file' in request.files:
            file = request.files['file']
            if not file.filename:
                return jsonify({'error': 'Nie wybrano pliku'}), 400
            
            # Save file temporarily
            file_path = os.path.join(UPLOAD_DIR, file.filename)
            file.save(file_path)
            
            # Parse file
            results = parser.parse_file(file_path)
        
        # Check if text data
        elif 'data' in request.json:
            text_data = request.json.get('data', '')
            if not text_data.strip():
                return jsonify({'error': 'Brak danych do przetworzenia'}), 400
            
            delimiter = request.json.get('delimiter', '\t')
            lines = [line for line in text_data.strip().split('\n') if line.strip()]
            
            # Użyj lokalnego parsera dla lepszej kompatybilności
            print(f"📝 Parsowanie lokalnie (Python Parser), {len(lines)} linii")
            results = parse_data_local(lines, delimiter)
            
            # Konwertuj na format parser_v2
            results = [type('MockResult', (), {
                'record_id': r['id'],
                'status': type('Status', (), {'value': 'SUCCESS'})(),
                'confidence': 0.95,
                'parent_data': type('ParentData', (), {
                    'father_name': r['fatherName'],
                    'father_surname': r['fatherSurname'],
                    'father_age': r['fatherAge'],
                    'mother_name': r['motherName'],
                    'mother_surname': r['motherSurname'],
                    'mother_age': r['motherAge'],
                    'place': r['place'],  # Zmienione z origin_place na place
                    'year': r['year'],
                    'number': r['number'],
                    'surname': r['surname'],
                    'name': r['name'],
                    'notes': r['notes'],
                    'original': r['original']
                })(),
                'warnings': [],
                'original_text': r['original']
            })() for r in results]
            
            # DEBUG: Pokaż pierwszy rekord
            if results:
                first = results[0]
                print(f"🔍 DEBUG pierwszy rekord po konwersji:")
                print(f"   record_id: {first.record_id}")
                print(f"   fatherName: {first.parent_data.father_name}")
                print(f"   place: {first.parent_data.place}")
                print(f"   notes: {first.parent_data.notes[:50] if first.parent_data.notes else 'brak'}")
        
        else:
            return jsonify({'error': 'Nie znaleziono danych (file lub data)'}), 400
        
        # Validate against database
        validated_results = validate_results(results)
        
        # Prepare response - dodaj nowe pola
        response_data = [
            {
                'record_id': r.record_id,
                'status': r.status.value if hasattr(r.status, 'value') else str(r.status),
                'confidence': r.confidence,
                'parent_data': {
                    'father_name': getattr(r.parent_data, 'father_name', ''),
                    'father_surname': getattr(r.parent_data, 'father_surname', ''),
                    'father_age': getattr(r.parent_data, 'father_age', ''),
                    'father_birth_est': getattr(r.parent_data, 'father_birth_est', ''),
                    'father_occupation': getattr(r.parent_data, 'father_occupation', ''),
                    'mother_name': getattr(r.parent_data, 'mother_name', ''),
                    'mother_surname': getattr(r.parent_data, 'mother_surname', ''),
                    'mother_age': getattr(r.parent_data, 'mother_age', ''),
                    'mother_birth_est': getattr(r.parent_data, 'mother_birth_est', ''),
                    'mother_occupation': getattr(r.parent_data, 'mother_occupation', ''),
                    'origin_place': getattr(r.parent_data, 'origin_place', ''),
                    'child_relation': getattr(r.parent_data, 'child_relation', ''),
                    'year': getattr(r.parent_data, 'year', ''),
                    'number': getattr(r.parent_data, 'number', ''),
                    'surname': getattr(r.parent_data, 'surname', ''),
                    'name': getattr(r.parent_data, 'name', ''),
                    'notes': getattr(r.parent_data, 'notes', ''),
                    'original': getattr(r.parent_data, 'original', '')
                },
                'validation': validated_results.get(r.record_id, {}),
                'warnings': r.warnings if hasattr(r, 'warnings') else [],
                'original_text': r.original_text if hasattr(r, 'original_text') else ''
            }
            for r in results
        ]
        
        # Summary statistics
        stats = {
            'total': len(results),
            'success': sum(1 for r in results if r.status == ParsingStatus.SUCCESS),
            'partial': sum(1 for r in results if r.status == ParsingStatus.PARTIAL),
            'anomaly': sum(1 for r in results if r.status == ParsingStatus.ANOMALY),
            'empty': sum(1 for r in results if r.status == ParsingStatus.EMPTY),
            'avg_confidence': sum(r.confidence for r in results) / len(results) if results else 0
        }
        
        return jsonify({
            'success': True,
            'records': response_data,
            'stats': stats,
            'message': f'Przetworzono {len(results)} rekordów'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def validate_results(results):
    """
    Waliduje wyniki parsowania względem bazy imion/nazwisk
    Zwraca dict z flagami walidacji dla każdego rekordu
    """
    validation = {}
    
    for result in results:
        record_validation = {
            'father_name_valid': result.parent_data.father_name in NAME_DATABASE['male_names'],
            'father_surname_valid': result.parent_data.father_surname in NAME_DATABASE['male_surnames'],
            'mother_name_valid': result.parent_data.mother_name in NAME_DATABASE['female_names'],
            'mother_surname_valid': result.parent_data.mother_surname in NAME_DATABASE['female_surnames'],
        }
        validation[result.record_id] = record_validation
    
    return validation

@app.route('/api/table', methods=['POST'])
def generate_table():
    """
    Generuje HTML tabeli na podstawie rekordów
    POST body: {'records': [list], 'filters': {'red': bool, 'green': bool, 'gray': bool}}
    """
    try:
        request_data = request.json
        records = request_data.get('records', [])
        filters = request_data.get('filters', {'red': True, 'green': True, 'gray': True})
        
        if not records:
            return jsonify({'html': '<tr><td colspan="16">Brak danych</td></tr>'})
        
        rows_html = []
        
        for record in records:
            # Waliduj rekord (jeśli nie ma flag walidacji lub są False)
            validate_record_local(record)
            
            try:
                # Oblicz status rekordu
                has_data = any([record.get('fatherName'), record.get('fatherSurname'), 
                               record.get('motherName'), record.get('motherSurname')])
                
                if not has_data:
                    status = 'empty'
                else:
                    is_fully_validated = all([
                        record.get('fatherNameValidated', False),
                        record.get('fatherSurnameValidated', False),
                        record.get('motherNameValidated', False),
                        record.get('motherSurnameValidated', False)
                    ])
                    status = 'validated' if is_fully_validated else 'warning'
                
                # Filtry
                if status == 'warning' and not filters.get('red', True):
                    continue
                if status == 'validated' and not filters.get('green', True):
                    continue
                if status == 'empty' and not filters.get('gray', True):
                    continue
                
                # Klasa CSS dla wiersza
                row_class = f"row-{status}"
                
                # Pełna linia oryginalna dla tooltip z separatorem ⁂
                original_line = '⁂'.join([
                    str(record.get('id', '')),
                    str(record.get('year', '')),
                    str(record.get('number', '')),
                    str(record.get('surname', '')),
                    str(record.get('name', '')),
                    str(record.get('place', '')),
                    str(record.get('fatherName', '')),
                    str(record.get('fatherSurname', '')),
                    str(record.get('fatherAge', '')),
                    str(record.get('motherName', '')),
                    str(record.get('motherSurname', '')),
                    str(record.get('motherAge', '')),
                    str(record.get('notes', ''))
                ])
                
                # Funkcja do kolorowania komórek z rozszerzoną logiką
                def cell_class(field_name, field_value):
                    # Puste wartości
                    if not field_value or field_value == '-':
                        return 'text-empty'

                    # Użyj pre-komputowanych flag walidacji jeśli dostępne
                    validation_flag = f'{field_name}Validated'
                    if validation_flag in record:
                        if record[validation_flag]:
                            return 'text-validated'
                        elif field_value.strip():
                            return 'cell-not-found'
                        return ''

                    # Fallback: sprawdź bezpośrednio w bazie danych
                    normalized_value = field_value.lower()
                    if field_name == 'fatherName':
                        # Ojciec: TYLKO male_names (neutralne też są w male_names)
                        if normalized_value in NAME_DATABASE['male_names']:
                            return 'text-validated'
                    elif field_name == 'motherName':
                        # Matka: TYLKO female_names (neutralne też są w female_names)
                        if normalized_value in NAME_DATABASE['female_names']:
                            return 'text-validated'
                    elif field_name == 'name':
                        # Dziecko: wszystkie imiona
                        if normalized_value in NAME_DATABASE['all_names']:
                            return 'text-validated'
                    elif field_name == 'fatherSurname':
                        # Ojciec: TYLKO nazwiska męskie
                        if normalized_value in NAME_DATABASE['male_surnames']:
                            return 'text-validated'
                    elif field_name in ['motherSurname', 'motherMaidenName']:
                        # Matka: TYLKO nazwiska żeńskie
                        if normalized_value in NAME_DATABASE['female_surnames']:
                            return 'text-validated'
                    elif field_name == 'surname':
                        # Dziecko: wszystkie nazwiska
                        if normalized_value in NAME_DATABASE['all_surnames']:
                            return 'text-validated'
                    elif field_name == 'place':
                        # Miejscowość
                        if normalized_value in NAME_DATABASE['places']:
                            return 'text-validated'
                    elif field_name in ['fatherAge', 'motherAge']:
                        # Sprawdź wiek rodziców
                        if validate_parent_age(field_value) is True:
                            return 'text-validated'
                        elif validate_parent_age(field_value) is False:
                            return 'cell-not-found'

                    # Jeśli wartość niepusta ale nie znaleziona w bazie
                    if field_value.strip():
                        return 'cell-not-found'

                    return ''
                
                # Funkcja do dodawania edytowalności
                def editable_class(is_editable):
                    return 'cell-editable' if is_editable else ''
                
                cells = [
                    f'<td class="sticky-col">{record.get("id", "-")}</td>',
                    f'<td>{record.get("year", "-")}</td>',
                    f'<td>{record.get("number", "-")}</td>',
                    f'<td class="{cell_class("surname", record.get("surname", "-"))}">{record.get("surname", "-")}</td>',
                    f'<td class="{cell_class("name", record.get("name", "-"))}">{record.get("name", "-")}</td>',
                    f'<td class="{cell_class("place", record.get("place", "-"))}">{record.get("place", "-")}</td>',
                    f'<td class="{cell_class("fatherName", record.get("fatherName", "-"))} cell-editable" onclick="startInlineEdit(this, \'fatherName\', \'{record.get("id", "")}\')">{ record.get("fatherName", "-")}</td>',
                    f'<td class="{cell_class("fatherSurname", record.get("fatherSurname", "-"))} cell-editable" onclick="startInlineEdit(this, \'fatherSurname\', \'{record.get("id", "")}\')">{ record.get("fatherSurname", "-")}</td>',
                    f'<td class="{cell_class("fatherAge", record.get("fatherAge", "-"))} cell-editable" onclick="startInlineEdit(this, \'fatherAge\', \'{record.get("id", "")}\')">{ record.get("fatherAge", "-")}</td>',
                    f'<td class="{cell_class("motherName", record.get("motherName", "-"))} cell-editable" onclick="startInlineEdit(this, \'motherName\', \'{record.get("id", "")}\')">{ record.get("motherName", "-")}</td>',
                    f'<td class="{cell_class("motherSurname", record.get("motherSurname", "-"))} cell-editable" onclick="startInlineEdit(this, \'motherSurname\', \'{record.get("id", "")}\')">{ record.get("motherSurname", "-")}</td>',
                    f'<td class="{cell_class("motherAge", record.get("motherAge", "-"))} cell-editable" onclick="startInlineEdit(this, \'motherAge\', \'{record.get("id", "")}\')">{ record.get("motherAge", "-")}</td>',
                    f'<td>{record.get("notes", "-")}</td>',
                    f'<td title="{original_line}">{original_line[:50]}...</td>',
                    f'<td><button class="btn btn-small" onclick="openEditModal(\'{record.get("id", "")}\')"><span class="material-icons" style="font-size: 16px;">edit</span></button></td>'
                ]
                
                rows_html.append(f'<tr class="{row_class}">{"".join(cells)}</tr>')
            except Exception as record_error:
                print(f"Błąd przetwarzania rekordu {record.get('id', 'unknown')}: {record_error}")
                continue  # Pomiń błędny rekord
        
        return jsonify({
            'success': True,
            'html': '\n'.join(rows_html),
            'filtered_count': len(rows_html),
            'total_count': len(records)
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/validate', methods=['POST'])
def validate_records():
    """
    Waliduje rekordy względem bazy imion/nazwisk
    POST body: {'records': [list of records]}
    """
    try:
        request_data = request.json
        records = request_data.get('records', [])
        
        if not records:
            return jsonify({'error': 'Brak rekordów do walidacji'}), 400
        
        validated_records = []
        stats = {
            'total': len(records),
            'confirmed': 0,
            'warning': 0,
            'empty': 0,
            'progress': 0
        }
        
        for record in records:
            # Walidacja imion, nazwisk i miejscowości (case-insensitive)
            child_name = record.get('name', '').lower() if record.get('name') else ''
            child_surname = record.get('surname', '').lower() if record.get('surname') else ''
            place = record.get('place', '').lower() if record.get('place') else ''
            father_name = record.get('fatherName', '').lower() if record.get('fatherName') else ''
            father_surname = record.get('fatherSurname', '').lower() if record.get('fatherSurname') else ''
            mother_name = record.get('motherName', '').lower() if record.get('motherName') else ''
            mother_surname = record.get('motherSurname', '').lower() if record.get('motherSurname') else ''
            
            child_name_valid = child_name in NAME_DATABASE['all_names'] if child_name else False
            child_surname_valid = child_surname in NAME_DATABASE['all_surnames'] if child_surname else False
            place_valid = place in NAME_DATABASE['places'] if place else False
            father_name_valid = father_name in NAME_DATABASE['all_names'] if father_name else False
            father_surname_valid = father_surname in NAME_DATABASE['all_surnames'] if father_surname else False
            mother_name_valid = mother_name in NAME_DATABASE['all_names'] if mother_name else False
            mother_surname_valid = mother_surname in NAME_DATABASE['all_surnames'] if mother_surname else False
            
            # Walidacja wieku rodziców
            father_age_valid = validate_parent_age(record.get('fatherAge', ''))
            mother_age_valid = validate_parent_age(record.get('motherAge', ''))
            
            # Określ status rekordu
            has_data = bool(record.get('fatherName') or record.get('fatherSurname') or 
                          record.get('motherName') or record.get('motherSurname'))
            
            if not has_data:
                status = 'empty'
                stats['empty'] += 1
            elif father_name_valid and father_surname_valid and mother_name_valid and mother_surname_valid:
                status = 'validated'
                stats['confirmed'] += 1
            else:
                status = 'warning'
                stats['warning'] += 1
            
            validated_record = {
                **record,
                'nameValidated': child_name_valid,
                'surnameValidated': child_surname_valid,
                'placeValidated': place_valid,
                'fatherNameValidated': father_name_valid,
                'fatherSurnameValidated': father_surname_valid,
                'fatherAgeValidated': father_age_valid,
                'motherNameValidated': mother_name_valid,
                'motherSurnameValidated': mother_surname_valid,
                'motherAgeValidated': mother_age_valid,
                'motherMaidenNameValidated': mother_surname_valid,
                'status': status
            }
            validated_records.append(validated_record)
        
        # Oblicz postęp
        if stats['total'] > 0:
            stats['progress'] = int((stats['confirmed'] / stats['total']) * 100)
        
        return jsonify({
            'success': True,
            'records': validated_records,
            'stats': stats
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/validate-field', methods=['POST'])
def validate_single_field():
    """
    Walidacja pojedynczego pola - szybka usługa dla real-time podpowiedzi
    POST body: {
        'fieldType': 'name|surname|place',
        'value': 'wartość do walidacji',
        'context': {
            'recordType': 'baptism|death|marriage',
            'year': 'rok rekordu (opcjonalne)'
        }
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Brak danych JSON'}), 400
        
        field_type = data.get('fieldType', '').lower()
        value = data.get('value', '').strip()
        context = data.get('context', {})
        record_type = context.get('recordType', 'baptism')
        year = context.get('year')
        
        if not field_type or not value:
            return jsonify({'success': False, 'error': 'Brak wymaganych pól: fieldType, value'}), 400
        
        # Normalizacja wartości
        normalized_value = value.lower()
        
        # Wynik walidacji
        result = {
            'fieldType': field_type,
            'originalValue': value,
            'normalizedValue': normalized_value,
            'status': 'unknown',
            'color': 'gray',
            'message': '',
            'suggestions': []
        }
        
        # Walidacja imion
        if field_type == 'name':
            if normalized_value in NAME_DATABASE['all_names']:
                result['status'] = 'valid'
                result['color'] = 'green'
                result['message'] = 'Imię znalezione w bazie'
            else:
                result['status'] = 'invalid'
                result['color'] = 'red'
                result['message'] = 'Imię nie znalezione w bazie'
                
                # Znajdź podobne imiona (Levenshtein distance <= 2)
                suggestions = find_similar_items(normalized_value, NAME_DATABASE['all_names'], max_distance=2)
                if suggestions:
                    result['suggestions'] = suggestions[:5]  # Max 5 sugestii
                    result['message'] += f'. Sugestie: {", ".join(suggestions[:3])}'
        
        # Walidacja nazwisk
        elif field_type == 'surname':
            if normalized_value in NAME_DATABASE['all_surnames']:
                result['status'] = 'valid'
                result['color'] = 'green'
                result['message'] = 'Nazwisko znalezione w bazie'
            else:
                result['status'] = 'invalid'
                result['color'] = 'red'
                result['message'] = 'Nazwisko nie znalezione w bazie'
                
                # Znajdź podobne nazwiska
                suggestions = find_similar_items(normalized_value, NAME_DATABASE['all_surnames'], max_distance=2)
                if suggestions:
                    result['suggestions'] = suggestions[:5]
                    result['message'] += f'. Sugestie: {", ".join(suggestions[:3])}'
        
        # Walidacja miejscowości
        elif field_type == 'place':
            if normalized_value in NAME_DATABASE['places']:
                result['status'] = 'valid'
                result['color'] = 'green'
                result['message'] = 'Miejscowość znaleziona w bazie'
            else:
                result['status'] = 'invalid'
                result['color'] = 'red'
                result['message'] = 'Miejscowość nie znaleziona w bazie'
                
                # Znajdź podobne miejscowości
                suggestions = find_similar_items(normalized_value, NAME_DATABASE['places'], max_distance=2)
                if suggestions:
                    result['suggestions'] = suggestions[:5]
                    result['message'] += f'. Sugestie: {", ".join(suggestions[:3])}'
        
        # Walidacja wieku
        elif field_type == 'age':
            age_valid, age_message = validate_age(value, record_type, year)
            result['status'] = 'valid' if age_valid else 'invalid'
            result['color'] = 'green' if age_valid else 'red'
            result['message'] = age_message
        
        else:
            result['status'] = 'unknown'
            result['color'] = 'gray'
            result['message'] = f'Nieobsługiwany typ pola: {field_type}'
        
        return jsonify({
            'success': True,
            'validation': result
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def find_similar_items(target, item_set, max_distance=2):
    """
    Znajdź podobne elementy używając prostej odległości Levenshtein
    """
    def levenshtein_distance(s1, s2):
        if len(s1) < len(s2):
            return levenshtein_distance(s2, s1)
        if len(s2) == 0:
            return len(s1)
        
        previous_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    similar = []
    for item in item_set:
        distance = levenshtein_distance(target, item)
        if distance <= max_distance and distance > 0:  # distance > 0 aby wykluczyć identyczne
            similar.append((item, distance))
    
    # Sortuj po odległości, potem alfabetycznie
    similar.sort(key=lambda x: (x[1], x[0]))
    return [item for item, dist in similar]

def validate_age(age_str, record_type='baptism', year=None):
    """
    Kontekstowa walidacja wieku
    """
    try:
        # Parsuj wiek (obsługa formatów jak "40", "l.40", "~1801")
        age_match = re.search(r'(\d+)', str(age_str))
        if not age_match:
            return False, "Nieprawidłowy format wieku"
        
        age = int(age_match.group(1))
        
        # Bazowe zakresy wiekowe
        age_ranges = {
            'baptism': {'father': (18, 70), 'mother': (15, 50)},  # Chrzest
            'death': {'person': (0, 120)},  # Zgon - szeroki zakres
            'marriage': {'person': (18, 80)}  # Małżeństwo
        }
        
        # Dostosuj do epoki jeśli podano rok
        if year:
            try:
                year_int = int(year)
                # W starszych epokach oczekiwana długość życia była niższa
                if year_int < 1800:
                    age_ranges['death']['person'] = (0, 90)
                elif year_int < 1900:
                    age_ranges['death']['person'] = (0, 100)
            except:
                pass
        
        # Sprawdź zakres dla typu rekordu
        if record_type == 'baptism':
            # Dla chrztu sprawdzamy wiek rodziców
            if 'father' in age_str.lower() or 'ojciec' in age_str.lower():
                min_age, max_age = age_ranges['baptism']['father']
            elif 'mother' in age_str.lower() or 'matka' in age_str.lower():
                min_age, max_age = age_ranges['baptism']['mother']
            else:
                return False, "Dla chrztu podaj wiek ojca lub matki"
        elif record_type == 'death':
            min_age, max_age = age_ranges['death']['person']
        elif record_type == 'marriage':
            min_age, max_age = age_ranges['marriage']['person']
        else:
            min_age, max_age = (0, 150)  # Fallback
        
        if age < min_age:
            return False, f"Wiek {age} zbyt niski (min {min_age})"
        elif age > max_age:
            return False, f"Wiek {age} zbyt wysoki (max {max_age})"
        else:
            return True, f"Wiek {age} w prawidłowym zakresie"
            
    except Exception as e:
        return False, f"Błąd walidacji wieku: {str(e)}"

@app.route('/api/export/<format>', methods=['POST'])
def export_data(format):
    """
    Eksportuj przetworzne dane w wybranym formacie
    POST body: {
        'records': [...list of records...]
    }
    """
    try:
        request_data = request.json
        records = request_data.get('records', [])
        
        if not records:
            return jsonify({'error': 'Brak danych do eksportu'}), 400
        
        if format == 'json':
            # Return as JSON
            output = io.BytesIO(json.dumps(records, ensure_ascii=False, indent=2).encode('utf-8'))
            return send_file(
                output,
                mimetype='application/json',
                as_attachment=True,
                download_name=f'genealogy_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            )
        
        elif format == 'tsv':
            # Convert to TSV
            if not records:
                return jsonify({'error': 'Brak danych do eksportu'}), 400
            
            # Określona kolejność kolumn
            headers = ['id', 'year', 'number', 'surname', 'name', 'place', 
                      'fatherName', 'fatherSurname', 'fatherAge', 
                      'motherName', 'motherSurname', 'motherAge', 'notes', 'original']
            header_labels = ['ID', 'ROK', 'Nr', 'Nazwisko', 'Imię', 'Miejscowość',
                           'ImięO', 'NazwiskoO', 'wiekO', 'IM', 'NM', 'wM', 'uwagi', 'UWAGI ORG']
            
            lines = []
            # Header
            lines.append('\t'.join(header_labels))
            # Data rows
            for idx, record in enumerate(records):
                # Debug: pokaż pierwsze 3 rekordy
                if idx < 3:
                    print(f"DEBUG Export record {idx}: ID={record.get('id')}, fatherName={record.get('fatherName')}, motherName={record.get('motherName')}")
                
                # Zbuduj UWAGI ORG z separatorem ⁂ (nie TAB!)
                original_line = '⁂'.join([
                    str(record.get('id', '')),
                    str(record.get('year', '')),
                    str(record.get('number', '')),
                    str(record.get('surname', '')),
                    str(record.get('name', '')),
                    str(record.get('place', '')),
                    str(record.get('fatherName', '')),
                    str(record.get('fatherSurname', '')),
                    str(record.get('fatherAge', '')),
                    str(record.get('motherName', '')),
                    str(record.get('motherSurname', '')),
                    str(record.get('motherAge', '')),
                    str(record.get('notes', ''))
                ])
                
                values = []
                for key in headers:
                    if key == 'original':
                        # Użyj zbudowanej linii zamiast surowego original
                        values.append(original_line)
                    else:
                        val = record.get(key, '') if isinstance(record, dict) else getattr(record, key, '')
                        # Escapuj cudzysłowy i otocz wartość cudzysłowami jeśli zawiera TAB lub newline
                        val_str = str(val)
                        if '\t' in val_str or '\n' in val_str or '"' in val_str:
                            val_str = '"' + val_str.replace('"', '""') + '"'
                        values.append(val_str)
                lines.append('\t'.join(values))
            
            output = io.BytesIO('\n'.join(lines).encode('utf-8'))
            return send_file(
                output,
                mimetype='text/tab-separated-values',
                as_attachment=True,
                download_name=f'genealogy_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.tsv'
            )
        
        else:
            return jsonify({'error': f'Nieznany format: {format}'}), 400
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/export/tsv-backend', methods=['POST'])
def export_tsv_from_backend():
    """
    Eksportuj TSV bezpośrednio z danych backendu (te same co tabela 3)
    POST body: {'records': [list of MockResult objects from parser]}
    """
    try:
        request_data = request.json
        records = request_data.get('records', [])
        
        if not records:
            return 'Brak danych do eksportu', 400
        
        # Nagłówki
        headers = ['ID', 'ROK', 'Nr', 'Nazwisko', 'Imię', 'Miejscowość',
                   'ImięO', 'NazwiskoO', 'wiekO', 'IM', 'NM', 'wM', 'uwagi', 'UWAGI ORG']
        
        lines = ['\t'.join(headers)]
        
        # Konwertuj rekordy
        for record in records:
            # Pobierz dane z parent_data (record to MockResult object!)
            pd = record.parent_data
            
            # Zbuduj UWAGI ORG z separatorem ⁂
            original_line = '⁂'.join([
                str(record.record_id),
                str(pd.year),
                str(pd.number),
                str(pd.surname),
                str(pd.name),
                str(pd.place),
                str(pd.father_name),
                str(pd.father_surname),
                str(pd.father_age),
                str(pd.mother_name),
                str(pd.mother_surname),
                str(pd.mother_age),
                str(pd.notes)
            ])
            
            # Wiersz TSV
            values = [
                record.record_id,
                pd.year,
                pd.number,
                pd.surname,
                pd.name,
                pd.place,
                pd.father_name,
                pd.father_surname,
                pd.father_age,
                pd.mother_name,
                pd.mother_surname,
                pd.mother_age,
                pd.notes,
                original_line
            ]
            
            # Escapuj wartości (cudzysłów jeśli zawiera TAB, newline lub ")
            escaped_values = []
            for val in values:
                val_str = str(val)
                if '\t' in val_str or '\n' in val_str or '"' in val_str:
                    val_str = '"' + val_str.replace('"', '""') + '"'
                escaped_values.append(val_str)
            
            lines.append('\t'.join(escaped_values))
        
        # Zwróć TSV jako text
        return '\n'.join(lines), 200, {'Content-Type': 'text/tab-separated-values; charset=utf-8'}
    
    except Exception as e:
        print(f"❌ Błąd eksportu TSV: {e}")
        return f'Błąd eksportu: {str(e)}', 500

if __name__ == '__main__':
    print("Inicjalizacja Parent Validator Backend...")
    load_name_databases()
    
    print("\n" + "="*60)
    print("Server startuje na http://127.0.0.1:5000")
    print("="*60)
    print("\nDostępne endpoints:")
    print("  GET  /api/health - Status serwera")
    print("  POST /api/parse - Parsuj dane rodziców")
    print("  POST /api/validate - Waliduj rekordy")
    print("  POST /api/table - Generuj tabelę HTML")
    print("  POST /api/export/<format> - Eksportuj dane (json/tsv)")
    print("="*60 + "\n")
    
    app.run(debug=True, port=5000, host='0.0.0.0')
