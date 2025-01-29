
import logging
from pipedrive_helper import PipedriveHelper
import json
from datetime import datetime

logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_pipedrive():
    try:
        # Initialize PipedriveHelper
        pipedrive = PipedriveHelper('uniska')
        
        # Test data for organization
        test_data = {
            'ADR_NAME': 'Test Company GmbH',
            'STREET': 'Test Street',
            'HOUSE_NUMBER': '123',
            'PLZ': '8000',
            'ORT': 'Zürich',
            'LAND': 'CH',
            'AKP_VORNAME': 'John',
            'AKP_NAME': 'Doe',
            'AKP_MAIL': 'john.doe@test.com',
            'AKP_TEL': '+41 123 456 789',
            'NPO_ProjName': 'Test Project',
            'NPO_KDatum': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'NPO_KSumme': 10000,
            'NPO_ADatum': '2024-02-01 00:00:00'
        }

        # Test organization operations
        logger.info("Testing organization operations...")
        existing_org = pipedrive.find_organization_by_name(test_data['ADR_NAME'])
        
        if existing_org:
            logger.info(f"Found existing organization: {existing_org['name']}")
            org_id = existing_org['id']
        else:
            logger.info("Creating new organization...")
            org_result = pipedrive.create_organization(test_data)
            if not org_result.get('success'):
                raise Exception("Failed to create organization")
            org_id = org_result['data']['id']
            logger.info(f"Created organization with ID: {org_id}")

        # Test person operations
        logger.info("Testing person operations...")
        person_name = f"{test_data['AKP_VORNAME']} {test_data['AKP_NAME']}"
        existing_person = pipedrive.find_person_by_name(person_name, org_id)
        
        if existing_person:
            logger.info(f"Found existing person: {existing_person['name']}")
            person_id = existing_person['id']
        else:
            logger.info("Creating new person...")
            person_result = pipedrive.create_person(test_data, org_id)
            if not person_result.get('success'):
                raise Exception("Failed to create person")
            person_id = person_result['data']['id']
            logger.info(f"Created person with ID: {person_id}")

        # Test deal operations
        logger.info("Testing deal operations...")
        deal_result = pipedrive.create_deal(test_data, org_id)
        if deal_result.get('success'):
            logger.info(f"Created deal with ID: {deal_result['data']['id']}")
        else:
            raise Exception("Failed to create deal")

        # Test field retrieval
        logger.info("Testing field retrieval...")
        org_fields = pipedrive.get_organization_fields()
        person_fields = pipedrive.get_person_fields()
        deal_fields = pipedrive.get_deal_fields()
        
        logger.info(f"Retrieved {len(org_fields)} organization fields")
        logger.info(f"Retrieved {len(person_fields)} person fields")
        logger.info(f"Retrieved {len(deal_fields)} deal fields")

        return True

    except Exception as e:
        logger.error(f"Error in Pipedrive test: {str(e)}")
        return False

if __name__ == "__main__":
    test_pipedrive()
