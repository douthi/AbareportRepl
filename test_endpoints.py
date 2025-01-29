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

        return True

    except Exception as e:
        logger.error(f"Error in Pipedrive test: {str(e)}")
        return False

if __name__ == "__main__":
    test_pipedrive()