#!/usr/bin/env python3
import sys
import os
sys.path.append('.')

from backend import app
import json

def test_parse_endpoint():
    test_data = {
        'data': 'CH.LUB.BLIN.0001574\t1908\t001\tZyśko\tZofia\tBliżyn\tJózef\tZyśko\t40\tMaria\tKowalska\t35',
        'delimiter': '\t'
    }

    with app.test_client() as client:
        print("Testing /api/parse endpoint...")
        response = client.post('/api/parse',
                              data=json.dumps(test_data),
                              content_type='application/json')
        print(f'Response status: {response.status_code}')

        if response.status_code != 200:
            print(f'Error response: {response.data.decode()}')
            return False
        else:
            try:
                data = json.loads(response.data)
                records = data.get('records', [])
                print(f'Success: {len(records)} records parsed')
                if records:
                    print(f'First record ID: {records[0].get("record_id", "N/A")}')
                return True
            except Exception as e:
                print(f'Error parsing response: {e}')
                return False

if __name__ == '__main__':
    test_parse_endpoint()