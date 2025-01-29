
import requests
from pipedrive_helper import PipedriveHelper
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def fetch_and_display_data():
    pipedrive = PipedriveHelper('uniska')
    
    # Fetch organization with ID 965
    endpoint = f"{pipedrive.base_url}/organizations/965"
    params = {'api_token': pipedrive.api_key}
    response = requests.get(endpoint, params=params)
    if response.ok:
        org_data = response.json()['data']
        logger.info("\n=== Organization Details ===")
        logger.info(f"Organization Name: {org_data.get('name')}")
        logger.info(f"Address: {org_data.get('address')}")
    
    # Fetch person with ID 685
    endpoint = f"{pipedrive.base_url}/persons/685"
    params = {'api_token': pipedrive.api_key}
    response = requests.get(endpoint, params=params)
    if response.ok:
        person_data = response.json()['data']
        logger.info("\n=== Person Details ===")
        logger.info(f"Person Name: {person_data.get('name')}")
        logger.info(f"Email: {person_data.get('email')[0]['value'] if person_data.get('email') else 'N/A'}")
        logger.info(f"Phone: {person_data.get('phone')[0]['value'] if person_data.get('phone') else 'N/A'}")

    # Fetch deal with ID 359
    endpoint = f"{pipedrive.base_url}/deals/359"
    params = {'api_token': pipedrive.api_key}
    response = requests.get(endpoint, params=params)
    if response.ok:
        deal_data = response.json()['data']
        logger.info("\n=== Deal Details ===")
        logger.info(f"Deal Title: {deal_data.get('title')}")
        logger.info(f"Deal Value: {deal_data.get('value')} {deal_data.get('currency')}")
        logger.info(f"Status: {deal_data.get('status')}")

if __name__ == "__main__":
    fetch_and_display_data()
