import os
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

import logging
logger = logging.getLogger(__name__)

class PipedriveHelper:
    def __init__(self, company_key='uniska'):
        self.company_key = company_key
        env_key = f'{company_key.upper()}_PIPEDRIVE_API_KEY'
        self.api_key = os.getenv(env_key)
        logger.debug(f"Initializing PipedriveHelper for company: {company_key}")
        logger.debug(f"Looking for API key with env var: {env_key}")
        logger.debug(f"API key found: {bool(self.api_key)}")
        self.base_url = f'https://{company_key}ag.pipedrive.com/api/v1'
        self.mapping_file = f'mappings/{company_key}_field_mappings.json'
        os.makedirs('mappings', exist_ok=True)
        self._load_field_mappings()
        self.default_pipeline_id = self._get_default_pipeline_id()

    def _get_default_pipeline_id(self):
        """Get the ID of the default pipeline."""
        endpoint = f"{self.base_url}/pipelines"
        params = {'api_token': self.api_key}
        response = requests.get(endpoint, params=params)
        if response.ok:
            pipelines = response.json().get('data', [])
            if pipelines:
                return pipelines[0]['id']  # Return first pipeline ID
        return None

    def _format_timestamp(self, date_str):
        """Format timestamp to Pipedrive format (YYYY-MM-DD)."""
        if not date_str:
            return None
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
            return date_obj.strftime('%Y-%m-%d')
        except ValueError:
            return None

    def _load_field_mappings(self):
        """Load field mappings from config."""
        from config import Config
        self.field_mappings = Config.COMPANIES[self.company_key].get('field_mappings', [])

    def get_field_mappings(self):
        """Get current field mappings."""
        return self.field_mappings

    def find_organization_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Find organization by name."""
        if not name:
            return None
        endpoint = f"{self.base_url}/organizations/search"
        params = {
            'api_token': self.api_key,
            'term': name,
            'exact_match': True
        }
        response = requests.get(endpoint, params=params)
        if response.ok:
            items = response.json().get('data', {}).get('items', [])
            return items[0]['item'] if items else None
        return None

    def find_person_by_name(self, name: str, org_id: int) -> Optional[Dict[str, Any]]:
        """Find person by name and organization ID."""
        if not name:
            return None
        endpoint = f"{self.base_url}/persons/search"
        params = {
            'api_token': self.api_key,
            'term': name,
            'organization_id': org_id
        }
        response = requests.get(endpoint, params=params)
        if response.ok:
            items = response.json().get('data', {}).get('items', [])
            return items[0]['item'] if items else None
        return None

    def create_organization(self, data: Dict[str, Any]) -> Dict[str, Any]:
        endpoint = f"{self.base_url}/organizations"
        params = {'api_token': self.api_key}

        if not data.get('ADR_NAME'):
            raise ValueError("Organization name (ADR_NAME) is required")

        org_data = {}

        # Add mapped custom fields from field mappings
        for mapping in self.field_mappings:
            if mapping['entity'] == 'organization' and mapping['source'] in data:
                org_data[mapping['target']] = data[mapping['source']]

        # Ensure required name field is set
        if 'name' not in org_data:
            org_data['name'] = data['ADR_NAME'].strip()

        # Build address components
        address_parts = []
        if data.get('ADR_STREET'):
            address_parts.append(str(data['ADR_STREET']).strip())
        if data.get('ADR_HOUSE_NUMBER'):
            address_parts.append(str(data['ADR_HOUSE_NUMBER']).strip())

        if address_parts:
            org_data['address'] = ' '.join(address_parts)

        # Combine address fields into a single address field
        address_components = []
        if data.get('PLZ'):
            address_components.append(str(data['PLZ']).strip())
        if data.get('ORT'):
            address_components.append(str(data['ORT']).strip())
        if data.get('LAND'):
            address_components.append(str(data['LAND']).strip())

        if address_components:
            if org_data.get('address'):
                org_data['address'] += ', ' + ' '.join(address_components)
            else:
                org_data['address'] = ' '.join(address_components)

        logger.debug(f"Creating organization with data: {org_data}")
        try:
            response = requests.post(endpoint, params=params, json=org_data)
            result = response.json()
            logger.debug(f"Response from Pipedrive: {result}")
            if not response.ok or not result.get('success'):
                error_msg = result.get('error', 'Unknown error')
                logger.error(f"Pipedrive API error: {error_msg}")
                raise Exception(f"Pipedrive API error: {error_msg}")
            return result
        except requests.exceptions.RequestException as e:
            logger.error(f"Error creating organization: {str(e)}")
            raise Exception(f"Failed to create organization: {str(e)}")

    def create_person(self, data: Dict[str, Any], org_id: int) -> Dict[str, Any]:
        endpoint = f"{self.base_url}/persons"
        params = {'api_token': self.api_key}

        person_data = {'org_id': org_id}

        # Add mapped custom fields from field mappings
        person_fields = self.get_person_fields()
        field_types = {str(field['id']): {'type': field['field_type'], 'options': field.get('options', [])} 
                      for field in person_fields}

        for mapping in self.field_mappings:
            if mapping['entity'] == 'person' and mapping['source'] in data:
                field_value = data[mapping['source']]
                field_info = field_types.get(mapping['target'])

                if field_info and field_info['type'] == 'enum':
                    if mapping['source'] in ['ANR_ANREDE']:
                        # Map salutations directly as custom field
                        person_data[mapping['target']] = field_value
                    elif mapping['source'] == 'ANR_ANREDETEXT':
                        # Add Anredetext as custom field
                        person_data['2fea5d7de9997e5a2e32befbe45bf8a145373754'] = field_value
                else:
                    person_data[mapping['target']] = field_value

        # Set standard fields if not already mapped
        if 'name' not in person_data:
            person_data['name'] = f"{data.get('AKP_VORNAME', '')} {data.get('AKP_NAME', '')}".strip()
        if data.get('AKP_MAIL') and 'email' not in person_data:
            person_data['email'] = [{'value': data['AKP_MAIL'], 'primary': True}]
        if data.get('AKP_TEL') and 'phone' not in person_data:
            person_data['phone'] = [{'value': data['AKP_TEL'], 'primary': True}]

        logger.debug(f"Creating person with data: {person_data}")
        response = requests.post(endpoint, params=params, json=person_data)
        return response.json()

    def get_fields(self, entity_type: str) -> List[Dict[str, Any]]:
        """Get fields for a specific entity type."""
        endpoint = f"{self.base_url}/{entity_type}Fields"
        params = {
            'api_token': self.api_key,
            'start': 0,
            'limit': 100
        }

        response = requests.get(endpoint, params=params)
        if response.ok:
            data = response.json()
            fields = []
            for field in data.get('data', []):
                field_data = {
                    'key': field.get('key'),
                    'name': field.get('name'),
                    'field_type': field.get('field_type'),
                    'id': field.get('id'),
                    'mandatory_flag': field.get('mandatory_flag', False),
                    'options': field.get('options', [])
                }
                logger.debug(f"Found {entity_type} field: {field_data}")
                fields.append(field_data)
            return fields
        logger.error(f"Failed to get {entity_type} fields: {response.text}")
        return []

    def get_organization_fields(self) -> List[Dict[str, Any]]:
        return self.get_fields('organization')

    def get_person_fields(self) -> List[Dict[str, Any]]:
        return self.get_fields('person')

    def get_deal_fields(self) -> List[Dict[str, Any]]:
        return self.get_fields('deal')

    def get_recent_changes(self, since_timestamp: str, items: List[str] = None) -> Dict[str, Any]:
        """Get recent changes in Pipedrive."""
        endpoint = f"{self.base_url}/recents"
        params = {
            'api_token': self.api_key,
            'since_timestamp': since_timestamp,
            'items': ','.join(items) if items else None
        }
        response = requests.get(endpoint, params=params)
        return response.json()

    def update_organization(self, org_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing organization."""
        endpoint = f"{self.base_url}/organizations/{org_id}"
        params = {'api_token': self.api_key}
        response = requests.put(endpoint, params=params, json=data)
        return response.json()

    def update_person(self, person_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing person."""
        endpoint = f"{self.base_url}/persons/{person_id}"
        params = {'api_token': self.api_key}
        response = requests.put(endpoint, params=params, json=data)
        return response.json()

    def update_deal(self, deal_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing deal."""
        endpoint = f"{self.base_url}/deals/{deal_id}"
        params = {'api_token': self.api_key}
        response = requests.put(endpoint, params=params, json=data)
        return response.json()

    def create_deal(self, data: Dict[str, Any], org_id: int) -> Dict[str, Any]:
        from datetime import datetime, timedelta
        endpoint = f"{self.base_url}/deals"
        params = {'api_token': self.api_key}

        # Check if deal is older than 24 months
        try:
            deal_date = datetime.strptime(data.get('NPO_KDatum', ''), '%Y-%m-%d %H:%M:%S')
        except (ValueError, TypeError):
            deal_date = datetime.now()  # Default to current date if invalid
        two_years_ago = datetime.now() - timedelta(days=730)

        deal_data = {'org_id': org_id, 'pipeline_id': self.default_pipeline_id}

        # Add mapped custom fields from field mappings
        deal_fields = self.get_deal_fields()
        field_ids = {str(field['id']): field['key'] for field in deal_fields}

        for mapping in self.field_mappings:
            if mapping['entity'] == 'deal' and mapping['source'] in data:
                field_value = data[mapping['source']]
                if mapping['source'] in ['NPO_KDatum', 'NPO_ADatum']:
                    field_value = self._format_timestamp(field_value)

                # Validate field ID exists
                if mapping['target'] in field_ids:
                    logger.debug(f"Mapping field {mapping['source']} to {field_ids[mapping['target']]} ({mapping['target']})")
                    deal_data[mapping['target']] = field_value
                else:
                    logger.warning(f"Invalid field ID in mapping: {mapping['target']}")

        # Set standard fields if not already mapped
        if 'title' not in deal_data:
            deal_data['title'] = data.get('NPO_ProjName', '')
        if 'value' not in deal_data:
            deal_data['value'] = data.get('NPO_KSumme', 0)
        if 'currency' not in deal_data:
            deal_data['currency'] = 'CHF'
        if 'add_time' not in deal_data:
            deal_data['add_time'] = self._format_timestamp(data.get('NPO_KDatum'))
        if 'close_time' not in deal_data:
            deal_data['close_time'] = self._format_timestamp(data.get('NPO_ADatum'))

        # Set project number and other custom fields
        deal_fields = self.get_deal_fields()
        for mapping in self.field_mappings:
            if mapping['entity'] == 'deal' and mapping['source'] in data:
                field_value = data[mapping['source']]
                # For custom fields, we need to use the correct format
                if mapping['target'].startswith('5d300'):  # Custom field
                    deal_data[f'5d300cf82930e07f6107c7255fcd0dd550af7774'] = field_value
                else:
                    deal_data[mapping['target']] = field_value

        # Use ANR values from the passed data directly since they were already looked up
        anr_anrede = data.get('ANR_ANREDE')
        anr_anredetext = data.get('ANR_ANREDETEXT')
        if anr_anrede:
            deal_data['031ae26196cff3bf754a3fa9ff701f13c73113bf'] = anr_anrede
        if anr_anredetext:
            deal_data['2fea5d7de9997e5a2e32befbe45bf8a145373754'] = anr_anredetext


        # Find or create primary contact first
        primary_contact = None
        person_name = f"{data.get('AKP_VORNAME', '')} {data.get('AKP_NAME', '')}".strip()
        if person_name:
            existing_person = self.find_person_by_name(person_name, org_id)
            if existing_person:
                logger.info(f"Found existing primary contact: {existing_person['name']}")
                primary_contact = existing_person
                deal_data['person_id'] = existing_person['id']
            else:
                logger.info(f"Creating new primary contact: {person_name}")
                person_result = self.create_person(data, org_id)
                if person_result.get('success'):
                    primary_contact = person_result['data']
                    deal_data['person_id'] = person_result['data']['id']
                    logger.info(f"Created and linked primary contact with ID: {person_result['data']['id']}")
                else:
                    logger.warning(f"Failed to create primary contact: {person_result}")

        # Check if deal already exists to prevent duplicates
        proj_nr = data.get('NPO_ProjNr')
        if proj_nr:
            existing_deals = self.search_deals_by_custom_field('5d300cf82930e07f6107c7255fcd0dd550af7774', proj_nr)
            if existing_deals:
                logger.info(f"Deal with project number {proj_nr} already exists")
                return {'success': False, 'error': 'Deal already exists'}

        # Set initial deal value
        if data.get('NPO_ADatum'):
            deal_data.update({
                'value': data.get('NPO_ASumme', 0)
            })
        else:
            deal_data.update({
                'status': 'open',
                'value': data.get('NPO_KSumme', 0)
            })

        # Step 1: Create initial deal
        logger.debug(f"Creating deal with data: {deal_data}")
        response = requests.post(endpoint, params=params, json=deal_data)
        result = response.json()
        logger.debug(f"Initial deal creation response: {result}")

        if result.get('success'):
            deal_id = result['data']['id']
            update_endpoint = f"{self.base_url}/deals/{deal_id}"

            # Step 2: Handle status and dates based on conditions
            status = data.get('Status')
            asumme = data.get('NPO_ASumme')
            adatum = data.get('NPO_ADatum')
            kdatum = data.get('NPO_KDatum')
            status4_date = data.get('NPO_Status4')

            # First set the status with explicit time handling
            if asumme:
                status_data = {
                    'status': 'won',
                    'won_time': self._format_timestamp(adatum),
                    'lost_time': None  # Clear lost time for won deals
                }
            elif str(status) == '4':  # Convert status to string for comparison
                # Use status4_date as primary, fall back to kdatum if not available
                lost_date = status4_date if status4_date else kdatum
                status_data = {
                    'status': 'lost',
                    'lost_time': self._format_timestamp(lost_date),
                    'won_time': None  # Clear won time for lost deals
                }
            else:
                status_data = {
                    'status': 'open',
                    'won_time': None,
                    'lost_time': None  # Clear both times for open deals
                }

            # Update deal with status and time in one request
            logger.debug(f"Setting deal {deal_id} status data: {status_data}")
            status_response = requests.put(update_endpoint, params=params, json=status_data)
            if not status_response.ok:
                logger.error(f"Failed to update deal status: {status_response.text}")
                logger.error(f"Status response: {status_response.text}")
            status_response = requests.put(update_endpoint, params=params, json=status_data)

            # Update time fields based on status
            if status_response.ok:
                time_data = {}
                if status_data['status'] == 'won' and adatum:
                    time_data = {'won_time': adatum}
                    logger.debug(f"Setting deal {deal_id} won_time to {adatum}")
                elif status_data['status'] == 'lost' and status == '4' and status4_date:
                    time_data = {'lost_time': status4_date}
                    logger.debug(f"Setting deal {deal_id} lost_time to {status4_date}")

                if time_data:
                    response = requests.put(update_endpoint, params=params, json=time_data)
                    result = response.json()
                    logger.debug(f"Deal time update response: {result}")

        return result

    def update_won_dates(self):
        """Update won dates for all deals with ADatum."""
        endpoint = f"{self.base_url}/deals"
        params = {'api_token': self.api_key, 'status': 'won'}

        response = requests.get(endpoint, params=params)
        if response.ok:
            deals = response.json().get('data', [])
            for deal in deals:
                deal_id = deal['id']
                # Get deal details to check custom fields
                detail_response = requests.get(f"{endpoint}/{deal_id}", params={'api_token': self.api_key})
                if detail_response.ok:
                    deal_data = detail_response.json().get('data', {})
                    adatum = None

                    # Look for ADatum in custom fields
                    for field in self.field_mappings:
                        if field['entity'] == 'deal' and field['source'] == 'NPO_ADatum':
                            adatum = deal_data.get(field['target'])
                            break

                    if adatum:
                        formatted_date = self._format_timestamp(adatum)
                        if formatted_date:
                            update_data = {
                                'won_time': formatted_date
                            }
                            update_response = requests.put(
                                f"{endpoint}/{deal_id}",
                                params={'api_token': self.api_key},
                                json=update_data
                            )
                            logger.debug(f"Updated won dates for deal {deal_id}: {update_response.json()}")
    def search_deals_by_custom_field(self, field_key: str, value: str) -> List[Dict[str, Any]]:
        """Search deals by custom field value."""
        endpoint = f"{self.base_url}/deals/search"
        params = {
            'api_token': self.api_key,
            'term': value,
            'exact_match': True,
            'fields': field_key
        }
        response = requests.get(endpoint, params=params)
        if response.ok:
            return response.json().get('data', {}).get('items', [])
        return []

    def get_organization_contacts(self, org_id: int) -> List[Dict[str, Any]]:
        """Get all contacts associated with an organization."""
        endpoint = f"{self.base_url}/persons/search"
        params = {
            'api_token': self.api_key,
            'org_id': org_id
        }
        response = requests.get(endpoint, params=params)
        if response.ok:
            return response.json().get('data', [])
        return []
