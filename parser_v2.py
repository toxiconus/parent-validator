#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Parser danych genealogicznych z aktu chrztów
Obsługuje 5 formatów danych z akt chrztu (1783-1900)
Wspiera: s./c. (syn/córka), l.XX (wiek), ~YYYY (szacowana data), zawody
"""

import json
import sys
from dataclasses import dataclass, asdict
from enum import Enum
from typing import List, Optional, Dict, Tuple
import re

class ParsingStatus(Enum):
    SUCCESS = "SUKCES"
    PARTIAL = "częściowe"
    ANOMALY = "anomalia"
    EMPTY = "puste"

class RecordFormat(Enum):
    """Typy formatów wykrytych w ur akta doc.txt"""
    FORMAT_A = "prosty_historyczny"  # 1783-1796: ID|Nazwisko|Imię|Nr|Rok|Miejsce|Uwagi
    FORMAT_B = "pelny_z_rodzicami"   # 1826-1830: 15+ kolumn z pełnymi danymi rodziców
    FORMAT_C = "lista_bez_rodzicow"  # 1834-1839: ID|Nazwisko|Imię|Wiek|Rok|[puste]
    FORMAT_D = "tekstowy_slash"      # 1864-1899: Miejsce / Ojciec l.wiek i Matka l.wiek
    FORMAT_E = "mieszany"            # Pojedyncze linie z różnymi formatami

@dataclass
class ParentData:
    father_name: str = ""
    father_surname: str = ""
    mother_name: str = ""
    mother_surname: str = ""
    origin_place: str = ""
    father_occupation: str = ""
    mother_occupation: str = ""
    father_age: str = ""           # Format: "l.40" lub pusty
    mother_age: str = ""           # Format: "l.30" lub pusty
    father_birth_est: str = ""     # Format: "~ 1786" lub pusty
    mother_birth_est: str = ""     # Format: "~ 1796" lub pusty
    child_relation: str = ""       # "s." (syn) lub "c." (córka) lub pusty
    has_prefix_indicator: bool = False
    prefix_type: Optional[str] = None
    maiden_name_form: str = ""

@dataclass
class ParseResult:
    record_id: str
    status: ParsingStatus
    parent_data: ParentData
    original_text: str
    confidence: float
    warnings: List[str]

class ParentParser:
    def __init__(self):
        self.results: List[ParseResult] = []
        # Kompiluj regex'y - rozszerzone wzorce
        self.pattern_prefix = re.compile(r'^([cs])\.\s+(.+)', re.IGNORECASE | re.UNICODE)
        self.pattern_age = re.compile(r'l\.(\d+)', re.UNICODE)
        self.pattern_occupation = re.compile(r'\(([^)]+)\)', re.UNICODE)
        
        # Nowe wzorce dla ur akta doc.txt
        self.pattern_child_relation = re.compile(r'\b([sc])\.?\s+', re.UNICODE)  # s. lub c.
        self.pattern_birth_est = re.compile(r'~\s*(\d{4})', re.UNICODE)  # ~ 1786
        self.pattern_slash_parents = re.compile(
            r'(.+?)\s*/\s*(.+)',  # "Miejsce / dane rodziców"
            re.UNICODE
        )
        self.pattern_parent_with_age = re.compile(
            r'([A-ZĄĆĘŁŃÓŚŹŻa-ząćęłńóśźż]+)\s+l\.(\d+)',  # "Imię l.30"
            re.UNICODE
        )

    def detect_format(self, fields: List[str], notes: str) -> RecordFormat:
        """Wykryj format rekordu na podstawie liczby kolumn i zawartości"""
        field_count = len([f for f in fields if f.strip()])
        
        # Format B: 15+ kolumn z danymi rodziców (pełna data, wiek, ~rok)
        if field_count >= 13:
            # Sprawdź czy są typowe cechy Formatu B
            if any('~' in f for f in fields):
                return RecordFormat.FORMAT_B
            if any(re.match(r'\d{1,2}\.\d{1,2}\.\d{4}', f) for f in fields):  # Data DD.MM.YYYY
                return RecordFormat.FORMAT_B
        
        # Format D: tekst z "/" (Miejsce / Rodzice)
        if notes and '/' in notes and ' i ' in notes:
            return RecordFormat.FORMAT_D
        
        # Format A: prosty historyczny (7-9 kolumn, lata 1783-1796)
        if 7 <= field_count <= 9 and not notes:
            return RecordFormat.FORMAT_A
        
        # Format C: lista bez rodziców (tylko 4-5 kolumn wypełnionych)
        if field_count <= 5:
            return RecordFormat.FORMAT_C
        
        # Domyślnie mieszany
        return RecordFormat.FORMAT_E
    
    def parse_child_relation(self, notes: str) -> str:
        """Wyciągnij s. (syn) lub c. (córka) z uwag"""
        match = self.pattern_child_relation.search(notes)
        if match:
            relation = match.group(1).lower()
            return 's.' if relation == 's' else 'c.'
        return ""
    
    def parse_age_with_prefix(self, text: str) -> str:
        """Wyciągnij wiek w formacie l.XX"""
        match = self.pattern_age.search(text)
        return f"l.{match.group(1)}" if match else ""
    
    def parse_birth_estimate(self, text: str) -> str:
        """Wyciągnij szacowaną datę urodzenia ~ YYYY"""
        match = self.pattern_birth_est.search(text)
        return f"~ {match.group(1)}" if match else ""
    
    def parse_occupation_from_text(self, text: str) -> str:
        """Wyciągnij zawód z nawiasów"""
        match = self.pattern_occupation.search(text)
        return match.group(1).strip() if match else ""
    
    def parse_format_d_parents(self, notes: str) -> Tuple[str, str, str, str, str, str]:
        """
        Parsuj Format D: "Miejscowość / Ojciec l.wiek i Matka Nazwisko l.wiek"
        Returns: (place, father_name, father_age, mother_name, mother_surname, mother_age)
        """
        place = ''
        father_name = ''
        father_age = ''
        mother_name = ''
        mother_surname = ''
        mother_age = ''
        
        # Sprawdź czy jest separator "/"
        match = self.pattern_slash_parents.match(notes)
        if not match:
            return (place, father_name, father_age, mother_name, mother_surname, mother_age)
        
        place = match.group(1).strip()
        parents_part = match.group(2).strip()
        
        # Sprawdź czy są obaj rodzice (separator " i ")
        if ' i ' not in parents_part:
            return (place, father_name, father_age, mother_name, mother_surname, mother_age)
        
        # Podziel na ojca i matkę
        parts = parents_part.split(' i ', 1)
        father_part = parts[0].strip()
        mother_part = parts[1].strip() if len(parts) > 1 else ''
        
        # Parsuj część ojca: "Imię l.wiek (zawód)"
        if father_part:
            father_age = self.parse_age_with_prefix(father_part)
            # Usuń wiek i zawód, zostaje imię
            father_name = re.sub(r'\s*l\.\d+', '', father_part)
            father_name = re.sub(r'\s*\([^)]+\)', '', father_name).strip()
        
        # Parsuj część matki: "Imię Nazwisko l.wiek"
        if mother_part:
            mother_age = self.parse_age_with_prefix(mother_part)
            # Usuń wiek
            mother_clean = re.sub(r'\s*l\.\d+', '', mother_part).strip()
            # Ostatnie słowo to nazwisko
            mother_words = mother_clean.split()
            if len(mother_words) >= 2:
                mother_surname = mother_words[-1]
                mother_name = ' '.join(mother_words[:-1])
            elif len(mother_words) == 1:
                mother_name = mother_words[0]
        
        return (place, father_name, father_age, mother_name, mother_surname, mother_age)
    
    def parse_record(self, record_id: str, father_name: str, father_surname: str, 
                    mother_name: str, mother_surname: str, notes: str, 
                    father_age_raw: str = '', mother_age_raw: str = '',
                    all_fields: List[str] = None) -> ParseResult:
        """
        Parsuj pojedynczy rekord rodziców - wspiera 5 formatów
        """
        parent_data = ParentData()
        warnings = []
        confidence = 0.0
        
        # Oczyść dane
        father_name = father_name.strip() if father_name else ""
        father_surname = father_surname.strip() if father_surname else ""
        mother_name = mother_name.strip() if mother_name else ""
        mother_surname = mother_surname.strip() if mother_surname else ""
        notes = notes.strip() if notes else ""
        
        # Wykryj format
        if all_fields is None:
            all_fields = [record_id, father_name, father_surname, mother_name, mother_surname, notes]
        
        record_format = self.detect_format(all_fields, notes)
        
        # Parsuj wg formatu
        if record_format == RecordFormat.FORMAT_D and notes:
            # Format tekstowy "Miejsce / Rodzice"
            place, f_name, f_age, m_name, m_surname, m_age = self.parse_format_d_parents(notes)
            parent_data.origin_place = place
            parent_data.father_name = f_name or father_name
            parent_data.father_age = f_age
            parent_data.mother_name = m_name or mother_name
            parent_data.mother_surname = m_surname or mother_surname
            parent_data.mother_age = m_age
            # Nazwisko ojca = nazwisko dziecka (z rekordu)
            parent_data.father_surname = father_surname
        
        else:
            # Standardowe przypisanie
            parent_data.father_name = father_name
            parent_data.father_surname = father_surname
            parent_data.mother_name = mother_name
            parent_data.mother_surname = mother_surname
            
            # Formatuj wiek z parametrów father_age_raw i mother_age_raw
            if father_age_raw and father_age_raw.strip():
                age_str = father_age_raw.strip()
                # Jeśli już ma prefix "l." to nie dodawaj
                if not age_str.startswith('l.'):
                    parent_data.father_age = f"l.{age_str}"
                else:
                    parent_data.father_age = age_str
            
            if mother_age_raw and mother_age_raw.strip():
                age_str = mother_age_raw.strip()
                if not age_str.startswith('l.'):
                    parent_data.mother_age = f"l.{age_str}"
                else:
                    parent_data.mother_age = age_str
            
            # Parsuj wiek i szacowane daty z pól rodziców (Format B - fallback)
            if record_format == RecordFormat.FORMAT_B and all_fields and len(all_fields) > 10:
                # Kolumny 9, 10 = wiek ojca, szac. urodzenie ojca
                if len(all_fields) > 9 and all_fields[9] and not parent_data.father_age:
                    parent_data.father_age = f"l.{all_fields[9]}" if all_fields[9].strip() else ''
                if len(all_fields) > 10 and all_fields[10]:
                    parent_data.father_birth_est = all_fields[10] if all_fields[10].strip() else ''
                
                # Kolumny 13, 14 = wiek matki, szac. urodzenie matki
                if len(all_fields) > 13 and all_fields[13] and not parent_data.mother_age:
                    parent_data.mother_age = f"l.{all_fields[13]}" if all_fields[13].strip() else ''
                if len(all_fields) > 14 and all_fields[14]:
                    parent_data.mother_birth_est = all_fields[14] if all_fields[14].strip() else ''
        
        # Parsuj uwagi dla wszystkich formatów
        if notes:
            # Relacja dziecka (s./c.)
            parent_data.child_relation = self.parse_child_relation(notes)
            
            # Zawód z nawiasów
            occupation = self.parse_occupation_from_text(notes)
            if occupation:
                parent_data.father_occupation = occupation
            
            # Szacowana data urodzenia
            birth_est = self.parse_birth_estimate(notes)
            if birth_est:
                parent_data.father_birth_est = birth_est
            
            # Miejsce pochodzenia (jeśli nie w Format D)
            if record_format != RecordFormat.FORMAT_D:
                origin_match = re.search(r'z\s+([A-ZĄĆĘŁŃÓŚŹŻa-ząćęłńóśźż\s]+?)(?:\s+[,\.]|$)', notes, re.UNICODE)
                if origin_match:
                    parent_data.origin_place = origin_match.group(1).strip()
        
        # Determine status
        has_father = bool(father_name and father_surname)
        has_mother = bool(mother_name and mother_surname)
        
        if has_father and has_mother:
            status = ParsingStatus.SUCCESS
            confidence = 1.0
        elif has_father or has_mother:
            status = ParsingStatus.PARTIAL
            confidence = 0.8
        elif father_name or mother_name or father_surname or mother_surname:
            status = ParsingStatus.PARTIAL
            confidence = 0.5
        else:
            status = ParsingStatus.EMPTY
            confidence = 0.0
            if notes:
                warnings.append(f"Pole Uwagi zawiera tekst: '{notes[:50]}'")
            else:
                warnings.append("Brak danych o rodzicach")
        
        # Check for unknown father marker
        if father_name.lower() in ['?', 'x'] or father_surname.lower() in ['?', 'x']:
            warnings.append("Ojciec nieznany (X lub ?)")
            confidence *= 0.8
        
        return ParseResult(
            record_id=record_id,
            status=status,
            parent_data=parent_data,
            original_text=f"ojciec: {father_name} {father_surname}, matka: {mother_name} {mother_surname}",
            confidence=confidence,
            warnings=warnings
        )

    def parse_file(self, filepath: str) -> List[ParseResult]:
        """Parsuj plik z aktu chrztów"""
        self.results = []
        
        try:
            with open(filepath, 'r', encoding='utf-8-sig') as f:
                lines = f.readlines()
        except UnicodeDecodeError:
            with open(filepath, 'r', encoding='latin-1') as f:
                lines = f.readlines()
        
        if not lines:
            print(f"Błąd: plik {filepath} jest pusty")
            return []
        
        # Parse first line - check if it has headers
        first_line = lines[0].strip()
        has_headers = first_line.lower().startswith('id') or \
                     'nazwisko' in first_line.lower() or \
                     'imię' in first_line.lower()
        
        if has_headers:
            # Parse headers - dynamic mapping
            headers = [h.strip() for h in first_line.split('\t')]
            print(f"Znalezione nagłówki ({len(headers)}): {', '.join(headers)}")
            data_start_line = 1
            
            # Zbuduj mapowanie nazw kolumn na indeksy
            header_indices = {}
            for i, h in enumerate(headers):
                h_lower = h.lower()
                header_indices[h_lower] = i
        else:
            # No headers - use default column order
            print(f"Brak nagłówków - używam domyślnej kolejności kolumn")
            headers = None
            header_indices = {}
            data_start_line = 0
        
        # Parse records
        for i, line in enumerate(lines[data_start_line:], start=1):
            if i % 500 == 0:
                print(f"[{i}] Sparsowano {i} rekordów")
            
            fields = line.strip().split('\t')
            if len(fields) < 2:  # Skip empty lines
                continue
            
            # Funkcja pomocnicza do pobierania pola wg nazwy
            def get_field(possible_keys):
                if not header_indices:
                    # Fallback bez nagłówków - użyj indeksów
                    return ""
                # Najpierw szukaj dokładnego dopasowania
                for key in possible_keys:
                    if key in header_indices:
                        idx = header_indices[key]
                        return fields[idx] if idx < len(fields) else ""
                # Potem szukaj substring (dla bezpieczeństwa)
                for key in possible_keys:
                    for hdr_key, idx in header_indices.items():
                        if key in hdr_key and key != hdr_key:  # substring ale nie dokładne
                            return fields[idx] if idx < len(fields) else ""
                return ""
            
            # Jeśli mamy nagłówki - użyj dynamicznego mapowania
            if header_indices:
                record_id = get_field(['id'])
                surname = get_field(['nazwisko', 'surname'])
                name = get_field(['imię', 'imie', 'name', 'firstname'])
                number = get_field(['nr', 'number'])
                year = get_field(['rok', 'year'])
                date = get_field(['data', 'date'])
                place = get_field(['miejscowość', 'miejscowosc', 'place', 'miejsce'])
                
                # Dane rodziców
                father_name = get_field(['imięo', 'imieo', 'imię ojca', 'father name'])
                father_surname = get_field(['nazwiskoo', 'nazwisko ojca', 'father surname'])
                mother_name = get_field(['im', 'imię matki', 'mother name'])
                mother_surname = get_field(['nm', 'nazwisko matki', 'mother surname'])
                
                # Wiek rodziców - może być w kolumnach wiekO/wM (numeryczne)
                father_age_raw = get_field(['wieko', 'wiek ojca', 'father age'])
                mother_age_raw = get_field(['wm', 'wiek matki', 'mother age'])
                
                notes = get_field(['uwagi', 'notes', 'uwagi org'])
                
                # Pomiń puste linie
                if not record_id or record_id.strip() == '':
                    continue
                
                # Dla header-based parsing przekazujemy father_age_raw i mother_age_raw
                result = self.parse_record(
                    record_id, 
                    father_name, 
                    father_surname, 
                    mother_name, 
                    mother_surname, 
                    notes,
                    father_age_raw=father_age_raw,
                    mother_age_raw=mother_age_raw,
                    all_fields=fields
                )
                self.results.append(result)
            else:
                # Fallback: użyj indeksów (dla plików bez nagłówków)
                field_count = len(fields)
                
                # Wspólne pola dla wszystkich formatów (pierwsze 5 kolumn)
                record_id = fields[0] if field_count > 0 else ''
                surname = fields[1] if field_count > 1 else ''
                name = fields[2] if field_count > 2 else ''
                number = fields[3] if field_count > 3 else ''
                year = fields[4] if field_count > 4 else ''
                
                # Inicjalizuj zmienne
                date = ''
                place = ''
                father_name = ''
                father_surname = ''
                mother_name = ''
                mother_surname = ''
                notes = ''
                
                # Wykryj format na podstawie liczby kolumn
                if field_count >= 13:
                    # Format B: 15+ kolumn z pełnymi danymi rodziców
                    # ID|Nazwisko|Imię|Nr|Rok|Data|Miejsce|ImięO|NazwiskoO|WiekO|~RokO|ImięM|NazwiskoM|WiekM|~RokM|Uwagi
                    date = fields[5] if field_count > 5 else ''
                    place = fields[6] if field_count > 6 else ''
                    father_name = fields[7] if field_count > 7 else ''
                    father_surname = fields[8] if field_count > 8 else ''
                    # fields[9] = wiek ojca, fields[10] = ~ rok ojca (obsługiwane w parse_record)
                    mother_name = fields[11] if field_count > 11 else ''
                    mother_surname = fields[12] if field_count > 12 else ''
                    # fields[13] = wiek matki, fields[14] = ~ rok matki
                    notes = fields[15] if field_count > 15 else ''
                elif field_count >= 8:
                    # Format A/simple: 8 kolumn z tekstem rodziców w kolumnie 7
                    # ID|Nazwisko|Imię|Nr|Rok|Data|Miejsce|Uwagi (tekst o rodzicach)
                    date = fields[5] if field_count > 5 else ''
                    place = fields[6] if field_count > 6 else ''
                    notes = fields[7] if field_count > 7 else ''
                    # Dane rodziców mogą być w notes (Format D: "Miejsce / Rodzice")
                else:
                    # Za mało kolumn - pomiń
                    continue
                
                result = self.parse_record(
                    record_id, 
                    father_name, 
                    father_surname, 
                    mother_name, 
                    mother_surname, 
                    notes,
                    all_fields=fields
                )
                self.results.append(result)
        
        return self.results
    
    def export_json(self, filepath: str):
        """Eksportuj wyniki do JSON"""
        data = [
            {
                'record_id': r.record_id,
                'status': r.status.value,
                'confidence': r.confidence,
                'parent_data': asdict(r.parent_data),
                'original_text': r.original_text,
                'warnings': r.warnings
            }
            for r in self.results
        ]
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"[OK] Eksportowano {len(data)} rekordow do {filepath}")
    
    def print_summary(self):
        """Pokaż podsumowanie parsowania"""
        if not self.results:
            print("Brak wyników do podsumowania")
            return
        
        stats = {
            ParsingStatus.SUCCESS: 0,
            ParsingStatus.PARTIAL: 0,
            ParsingStatus.ANOMALY: 0,
            ParsingStatus.EMPTY: 0
        }
        
        all_warnings = {}
        
        for result in self.results:
            stats[result.status] += 1
            for warning in result.warnings:
                all_warnings[warning] = all_warnings.get(warning, 0) + 1
        
        total = len(self.results)
        avg_confidence = sum(r.confidence for r in self.results) / total if total > 0 else 0
        
        print("\n" + "=" * 60)
        print("PODSUMOWANIE PARSOWANIA")
        print("=" * 60)
        print(f"Razem rekordow:        {total}")
        print(f"  [OK] Sukces (pelne):    {stats[ParsingStatus.SUCCESS]:6d} ({100*stats[ParsingStatus.SUCCESS]/total:.1f}%)")
        print(f"  [!!] Czesciowe:         {stats[ParsingStatus.PARTIAL]:6d} ({100*stats[ParsingStatus.PARTIAL]/total:.1f}%)")
        print(f"  [XX] Anomalie:          {stats[ParsingStatus.ANOMALY]:6d} ({100*stats[ParsingStatus.ANOMALY]/total:.1f}%)")
        print(f"  [  ] Puste:             {stats[ParsingStatus.EMPTY]:6d} ({100*stats[ParsingStatus.EMPTY]/total:.1f}%)")
        print(f"\nSrednia pewnosc:        {100*avg_confidence:.2f}%")
        
        if all_warnings:
            print(f"\nTop ostrzezen:")
            for warning, count in sorted(all_warnings.items(), key=lambda x: -x[1])[:10]:
                print(f"  - {warning}: {count}x")
        
        print("=" * 60)

def main():
    if len(sys.argv) < 2:
        print("Użycie: python parser_v2.py <plik_danych> [--json <plik_wyjściowy>]")
        sys.exit(1)
    
    data_file = sys.argv[1]
    json_output = None
    
    # Parse arguments
    if '--json' in sys.argv:
        idx = sys.argv.index('--json')
        if idx + 1 < len(sys.argv):
            json_output = sys.argv[idx + 1]
    
    # Parse
    parser = ParentParser()
    print(f"Parsowanie pliku: {data_file}")
    parser.parse_file(data_file)
    parser.print_summary()
    
    # Export if requested
    if json_output:
        parser.export_json(json_output)
    
    # Show sample results
    print(f"\nPierwsze 3 rekordy ze statusem SUCCESS:")
    success_results = [r for r in parser.results if r.status == ParsingStatus.SUCCESS]
    for r in success_results[:3]:
        pd = r.parent_data
        print(f"\n{r.record_id}:")
        print(f"  Ojciec: {pd.father_name} {pd.father_surname}")
        print(f"  Matka: {pd.mother_name} {pd.mother_surname}")
        print(f"  Pewność: {100*r.confidence:.1f}%")
        if r.warnings:
            print(f"  Ostrzeżenia: {', '.join(r.warnings)}")

if __name__ == '__main__':
    main()
