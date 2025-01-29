
from pipedrive_helper import PipedriveHelper
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def fetch_and_display_data():
    pipedrive = PipedriveHelper('uniska')
    
    # Fetch recent deal
    logger.info("\n=== Recent Deal ===")
    recent_changes = pipedrive.get_recent_changes('2024-01-01', ['deal'])
    if recent_changes.get('data'):
        for item in recent_changes['data']:
            if item['item'] == 'deal':
                deal_data = item['data']
                logger.info(f"Deal Title: {deal_data.get('title')}")
                logger.info(f"Deal Value: {deal_data.get('value')} {deal_data.get('currency')}")
                logger.info(f"Project Number: {deal_data.get('846468')}")  # Replace with actual field ID
                logger.info(f"Status: {deal_data.get('status')}")
    
    # Fetch recent organization
    logger.info("\n=== Recent Organization ===")
    org_name = "Test Company GmbH"  # The name we used in test_sync.py
    org = pipedrive.find_organization_by_name(org_name)
    if org:
        logger.info(f"Organization Name: {org.get('name')}")
        logger.info(f"Address: {org.get('address')}")
    
    # Fetch recent person
    logger.info("\n=== Recent Person ===")
    if org:
        person = pipedrive.find_person_by_name("Thomas Weber", org['id'])
        if person:
            logger.info(f"Person Name: {person.get('name')}")
            logger.info(f"Email: {person.get('email')[0]['value'] if person.get('email') else 'N/A'}")
            logger.info(f"Phone: {person.get('phone')[0]['value'] if person.get('phone') else 'N/A'}")

if __name__ == "__main__":
    fetch_and_display_data()
