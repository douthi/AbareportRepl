
import requests
import json

test_data = {
    "NPO_ProjNr": "PRJ-2024-001",
    "NPO_ProjName": "Complete Test Project 2024",
    "NPO_KSumme": 50000,
    "NPO_KDatum": "2024-01-29 00:00:00",
    "NPO_ADatum": "2024-12-31 00:00:00",
    "ADR_NAME": "Test Company AG",
    "ADR_TEL": "+41 44 123 45 67",
    "ADR_LAND": "CH",
    "ADR_PLZ": "8000",
    "ADR_ORT": "Zürich",
    "ADR_STREET": "Teststrasse",
    "ADR_HOUSE_NUMBER": "42",
    "AKP_NAME": "Muster",
    "AKP_VORNAME": "Hans",
    "AKP_FUNKTION": "CEO",
    "AKP_TEL": "+41 79 123 45 67",
    "AKP_MAIL": "hans.muster@testcompany.ch",
    "ANR_ANREDE": "Herr",
    "ANR_ANREDETEXT": "Sehr geehrter Herr",
    "company_key": "uniska"
}

response = requests.post('http://0.0.0.0:5000/sync-to-pipedrive', 
                        json=test_data,
                        headers={'Content-Type': 'application/json'})

print(f"Status Code: {response.status_code}")
try:
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except requests.exceptions.JSONDecodeError:
    print(f"Raw response: {response.text}")
