from pipedrive_helper import PipedriveHelper
import logging

logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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
    'ANR_ANREDE': 'Herr',  # Will be mapped to enum value 1
    'Status': 'new'
}

if __name__ == '__main__':
    pipedrive = PipedriveHelper('uniska')

    # Create or update organization
    org_name = test_data.get('ADR_NAME')
    existing_org = pipedrive.find_organization_by_name(org_name)

    if existing_org:
        org_result = pipedrive.update_organization(existing_org['id'], test_data)
        org_id = existing_org['id']
    else:
        org_result = pipedrive.create_organization(test_data)
        if not org_result.get('success'):
            raise Exception('Failed to create organization')
        org_id = org_result['data']['id']

    # Create or update person
    person_name = f"{test_data.get('AKP_VORNAME', '')} {test_data.get('AKP_NAME', '')}".strip()
    existing_person = pipedrive.find_person_by_name(person_name, org_id)

    if existing_person:
        person_result = pipedrive.update_person(existing_person['id'], test_data)
    else:
        person_result = pipedrive.create_person(test_data, org_id)
        if not person_result.get('success'):
            raise Exception('Failed to create person')

    # Create deal
    deal_result = pipedrive.create_deal(test_data, org_id)
    if not deal_result.get('success'):
        raise Exception('Failed to create deal')

    print("Test sync completed successfully!")