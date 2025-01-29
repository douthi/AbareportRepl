import logging
from pipedrive_helper import PipedriveHelper
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
            'ADR_NAME': 'Test Company GmbH',  # Required field
            'STREET': 'Teststrasse',
            'HOUSE_NUMBER': '123',
            'PLZ': '8000',
            'ORT': 'Zürich',
            'LAND': 'CH'
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
                logger.error(f"Organization creation failed: {org_result}")
                raise Exception(f"Failed to create organization: {org_result}")
            org_id = org_result['data']['id']
            logger.info(f"Created organization with ID: {org_id}")

        # Test person operations
        logger.info("Testing person operations...")
        person_data = {
            'AKP_VORNAME': 'John',
            'AKP_NAME': 'Doe',
            'AKP_MAIL': 'john.doe@example.com',
            'AKP_TEL': '+41 123 456 789'
        }

        existing_person = pipedrive.find_person_by_name(f"{person_data['AKP_VORNAME']} {person_data['AKP_NAME']}", org_id)

        if existing_person:
            logger.info(f"Found existing person: {existing_person['name']}")
        else:
            logger.info("Creating new person...")
            person_result = pipedrive.create_person(person_data, org_id)
            if not person_result.get('success'):
                logger.error(f"Person creation failed: {person_result}")
                raise Exception(f"Failed to create person: {person_result}")
            logger.info(f"Created person with ID: {person_result['data']['id']}")

        return True

    except Exception as e:
        logger.error(f"Error in Pipedrive test: {str(e)}")
        return False

if __name__ == "__main__":
    test_pipedrive()