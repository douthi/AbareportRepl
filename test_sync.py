from pipedrive_helper import PipedriveHelper
import logging

logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Test data with different values
test_data = {
    'NPO_ProjNr': '2024001',
    'NPO_ProjName': 'Solar Installation Project 2024',
    'NPO_KDatum': '2024-01-15 00:00:00',
    'NPO_KSumme': 85000.00,
    'NPO_ADatum': '2024-06-30 00:00:00',
    'NPO_ASumme': 90000.00,
    'ADR_NAME': 'SunTech Solutions AG',
    'ADR_TEL': '+41 44 555 6677',
    'ADR_LAND': 'Switzerland',
    'ADR_PLZ': '8002',
    'ADR_ORT': 'Zürich',
    'ADR_STREET': 'Seestrasse',
    'ADR_HOUSE_NUMBER': '123',
    'AKP_NAME': 'Schmidt',
    'AKP_VORNAME': 'Anna',
    'AKP_FUNKTION': 'Sales Director',
    'AKP_TEL': '+41 79 888 9999',
    'AKP_MAIL': 'anna.schmidt@suntech.ch',
    'ANR_ANREDE': 'Frau',
    'ANR_ANREDETEXT': 'Mrs',
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