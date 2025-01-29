
from pipedrive_helper import PipedriveHelper
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def fetch_and_display_data():
    pipedrive = PipedriveHelper('uniska')
    
    # Fetch deal with project number
    deal_fields = pipedrive.get_deal_fields()
    logger.info("\n=== Deal Fields ===")
    for field in deal_fields:
        logger.info(f"{field['name']} (ID: {field['id']}): {field['field_type']}")
    
    # Fetch person fields
    person_fields = pipedrive.get_person_fields()
    logger.info("\n=== Person Fields ===")
    for field in person_fields:
        logger.info(f"{field['name']} (ID: {field['id']}): {field['field_type']}")
        if field['field_type'] == 'enum':
            logger.info(f"Options: {field['options']}")
            
    # Fetch organization fields
    org_fields = pipedrive.get_organization_fields()
    logger.info("\n=== Organization Fields ===")
    for field in org_fields:
        logger.info(f"{field['name']} (ID: {field['id']}): {field['field_type']}")

if __name__ == "__main__":
    fetch_and_display_data()
