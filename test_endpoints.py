
import logging
from pipedrive_helper import PipedriveHelper

logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_pipedrive():
    try:
        # Initialize PipedriveHelper
        pipedrive = PipedriveHelper('uniska')
        
        # Test data
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
            'NPO_KDatum': '2024-01-01 00:00:00',
            'NPO_KSumme': 10000,
            'NPO_ADatum': '2024-02-01 00:00:00'
        }

        # 1. Test organization creation
        logger.info("Testing organization creation...")
        org_result = pipedrive.create_organization(test_data)
        if org_result.get('success'):
            org_id = org_result['data']['id']
            logger.info(f"Organization created with ID: {org_id}")

            # 2. Test person creation
            logger.info("Testing person creation...")
            person_result = pipedrive.create_person(test_data, org_id)
            if person_result.get('success'):
                logger.info(f"Person created with ID: {person_result['data']['id']}")

            # 3. Test deal creation
            logger.info("Testing deal creation...")
            deal_result = pipedrive.create_deal(test_data, org_id)
            if deal_result.get('success'):
                logger.info(f"Deal created with ID: {deal_result['data']['id']}")

        return True

    except Exception as e:
        logger.error(f"Error in Pipedrive test: {str(e)}")
        return False

if __name__ == "__main__":
    test_pipedrive()
