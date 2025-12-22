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

app = Flask(__name__)
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:8000", "http://127.0.0.1:8000", "http://localhost:8080", "http://127.0.0.1:8080", "http://localhost:5000"],
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
    'all_surnames': set()
}

def load_name_databases():
    """Załaduj bazy imion i nazwisk"""
    global NAME_DATABASE
    
    data_files = {
        'male_names': '../../../data/imiona_meskie.json',
        'female_names': '../../../data/imiona_zenskie.json',
        'all_names': '../../../data/imiona_wszystkie.json',
        'male_surnames': '../../../data/nazwiska_meskie.json',
        'female_surnames': '../../../data/nazwiska_zenskie.json',
        'all_surnames': '../../../data/nazwiska_wszystkie.json'
    }
    
    for key, path in data_files.items():
        full_path = os.path.join(DATA_DIR, path)
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                NAME_DATABASE[key] = set(data) if isinstance(data, list) else set(data.keys())
                print(f"✓ Załadowano {len(NAME_DATABASE[key])} {key}")
        except Exception as e:
            print(f"⚠ Nie udało się załadować {key}: {e}")

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
            
            # Parse as TSV text
            lines = text_data.strip().split('\n')
            delimiter = request.json.get('delimiter', '\t')
            
            # Parse manually here since parse_file expects file
            # For now, save to temp file
            temp_file = os.path.join(UPLOAD_DIR, f'temp_{datetime.now().timestamp()}.txt')
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(text_data)
            
            results = parser.parse_file(temp_file)
            os.remove(temp_file)
        
        else:
            return jsonify({'error': 'Nie znaleziono danych (file lub data)'}), 400
        
        # Validate against database
        validated_results = validate_results(results)
        
        # Prepare response - dodaj nowe pola
        response_data = [
            {
                'record_id': r.record_id,
                'status': r.status.value,
                'confidence': r.confidence,
                'parent_data': {
                    'father_name': r.parent_data.father_name,
                    'father_surname': r.parent_data.father_surname,
                    'father_age': r.parent_data.father_age,
                    'father_birth_est': r.parent_data.father_birth_est,
                    'father_occupation': r.parent_data.father_occupation,
                    'mother_name': r.parent_data.mother_name,
                    'mother_surname': r.parent_data.mother_surname,
                    'mother_age': r.parent_data.mother_age,
                    'mother_birth_est': r.parent_data.mother_birth_est,
                    'mother_occupation': r.parent_data.mother_occupation,
                    'origin_place': r.parent_data.origin_place,
                    'child_relation': r.parent_data.child_relation,
                },
                'validation': validated_results.get(r.record_id, {}),
                'warnings': r.warnings
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
            'father_name_valid': result.parent_data.father_name in NAME_DATABASE['all_names'],
            'father_surname_valid': result.parent_data.father_surname in NAME_DATABASE['all_surnames'],
            'mother_name_valid': result.parent_data.mother_name in NAME_DATABASE['all_names'],
            'mother_surname_valid': result.parent_data.mother_surname in NAME_DATABASE['all_surnames'],
        }
        validation[result.record_id] = record_validation
    
    return validation

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
            
            # Get all keys from first record
            keys = records[0].keys() if isinstance(records[0], dict) else []
            
            lines = []
            # Header
            lines.append('\t'.join(keys))
            # Data rows
            for record in records:
                values = []
                for key in keys:
                    if isinstance(record, dict):
                        val = record.get(key, '')
                    else:
                        val = getattr(record, key, '')
                    values.append(str(val))
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

if __name__ == '__main__':
    print("Inicjalizacja Parent Validator Backend...")
    load_name_databases()
    
    print("\n" + "="*60)
    print("Server startuje na http://127.0.0.1:5000")
    print("="*60)
    print("\nDostępne endpoints:")
    print("  GET  /api/health - Status serwera")
    print("  POST /api/parse - Parsuj dane rodziców")
    print("  POST /api/export/<format> - Eksportuj dane (json/tsv)")
    print("="*60 + "\n")
    
    app.run(debug=True, port=5000, host='0.0.0.0')
