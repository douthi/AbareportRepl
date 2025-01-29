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
        self.api_key = os.getenv(f'{company_key.upper()}_PIPEDRIVE_API_KEY')
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
        """Load field mappings from file."""
        try:
            with open(self.mapping_file, 'r') as f:
                self.field_mappings = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.field_mappings = []

    def save_field_mappings(self, mappings):
        """Save field mappings to file."""
        with open(self.mapping_file, 'w') as f:
            json.dump(mappings, f, indent=2)
        self.field_mappings = mappings

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
        if data.get('STREET'):
            address_parts.append(str(data['STREET']).strip())
        if data.get('HOUSE_NUMBER'):
            address_parts.append(str(data['HOUSE_NUMBER']).strip())
        
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
        for mapping in self.field_mappings:
            if mapping['entity'] == 'person' and mapping['source'] in data:
                person_data[mapping['target']] = data[mapping['source']]
                
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
                    'mandatory_flag': field.get('mandatory_flag', False),
                    'options': field.get('options', [])
                }
                fields.append(field_data)
            return fields
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
        for mapping in self.field_mappings:
            if mapping['entity'] == 'deal' and mapping['source'] in data:
                field_value = data[mapping['source']]
                if mapping['source'] in ['NPO_KDatum', 'NPO_ADatum']:
                    field_value = self._format_timestamp(field_value)
                deal_data[mapping['target']] = field_value
                
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

        if deal_date < two_years_ago:
            deal_data.update({
                'status': 'lost',
                'lost_reason': 'Aged out',
                'lost_time': '2025-01-01'
            })
        else:
            deal_data['status'] = 'open'

        logger.debug(f"Creating deal with data: {deal_data}")
        response = requests.post(endpoint, params=params, json=deal_data)
        result = response.json()
        logger.debug(f"Deal creation response: {result}")
        return result