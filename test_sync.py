
from pipedrive_helper import PipedriveHelper

# Test data with different values
test_data = {
    'NPO_ProjNr': 'PRJ-2024-001',
    'NPO_ProjName': 'Solar Installation Project',
    'NPO_KDatum': '2024-01-15',
    'NPO_KSumme': 75000.00,
    'NPO_ADatum': '2024-06-30',
    'NPO_ASumme': 80000.00,
    'ADR_NAME': 'EcoTech Solutions AG',
    'ADR_TEL': '+41 44 123 4567',
    'ADR_LAND': 'Switzerland',
    'ADR_PLZ': '8001',
    'ADR_ORT': 'Zürich',
    'ADR_STREET': 'Bahnhofstrasse',
    'ADR_HOUSE_NUMBER': '42',
    'AKP_NAME': 'Weber',
    'AKP_VORNAME': 'Thomas',
    'AKP_FUNKTION': 'Project Manager',
    'AKP_TEL': '+41 79 987 6543',
    'AKP_MAIL': 'thomas.weber@ecotech.ch',
    'AKP_ANR_NR': 1,  # Corresponds to "Herr" in ANR.csv
    'Status': 'new'
}

if __name__ == '__main__':
    pipedrive = PipedriveHelper('uniska')
    pipedrive.sync_to_pipedrive(test_data)
