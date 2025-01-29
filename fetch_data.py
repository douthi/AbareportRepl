import requests
import json
from pipedrive_helper import PipedriveHelper
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def search_deal_by_name(name):
    pipedrive = PipedriveHelper('uniska')
    endpoint = f"{pipedrive.base_url}/deals/search"
    params = {
        'api_token': pipedrive.api_key,
        'term': name,
        'exact_match': True
    }
    response = requests.get(endpoint, params=params)
    if response.ok:
        deals = response.json().get('data', {}).get('items', [])
        if deals:
            for deal in deals:
                logger.info(f"\n=== Found Deal ===")
                logger.info(f"Title: {deal['item'].get('title')}")
                logger.info(f"Value: {deal['item'].get('value')} {deal['item'].get('currency')}")
                logger.info(f"Status: {deal['item'].get('status')}")
                logger.info(f"ID: {deal['item'].get('id')}")
        else:
            logger.info("No deals found with that name")
    else:
        logger.error(f"Failed to search deals: {response.text}")

def fetch_and_display_data():
    pipedrive = PipedriveHelper('uniska')

    # Fetch deal with ID 359 and all its details
    deal_endpoint = f"{pipedrive.base_url}/deals/359"
    params = {'api_token': pipedrive.api_key}
    response = requests.get(deal_endpoint, params=params)
    if response.ok:
        deal_data = response.json()['data']
        logger.info("\n=== Complete Deal Details ===")
        logger.info(json.dumps(deal_data, indent=2))

        # Get linked person and organization IDs
        person_id = deal_data.get('person_id')
        org_id = deal_data.get('org_id')

        if person_id:
            person_endpoint = f"{pipedrive.base_url}/persons/{person_id}"
            response = requests.get(person_endpoint, params=params)
            if response.ok:
                person_data = response.json()['data']
                logger.info("\n=== Linked Person Details ===")
                logger.info(json.dumps(person_data, indent=2))
            else:
                logger.error(f"Failed to fetch person details: {response.text}")

        if org_id:
            org_endpoint = f"{pipedrive.base_url}/organizations/{org_id}"
            response = requests.get(org_endpoint, params=params)
            if response.ok:
                org_data = response.json()['data']
                logger.info("\n=== Linked Organization Details ===")
                logger.info(json.dumps(org_data, indent=2))
            else:
                logger.error(f"Failed to fetch organization details: {response.text}")
    else:
        logger.error(f"Failed to fetch deal details: {response.text}")


if __name__ == "__main__":
    search_deal_by_name("Solar Installation Project 2000")
    fetch_and_display_data()