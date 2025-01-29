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
        self.base_url = f'https://{company_key}ag.pipedrive.com/v1'
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

        org_data = {
            'name': data.get('NAME', ''),
            'address': f"{data.get('STREET', '')} {data.get('HOUSE_NUMBER', '')}".strip(),
            'address_postal_code': data.get('PLZ', ''),
            'address_city': data.get('ORT', ''),
            'address_country': data.get('LAND', '')
        }

        try:
            response = requests.post(endpoint, params=params, json=org_data)
            response.raise_for_status()
            result = response.json()
            if result.get('success'):
                return result
            raise Exception(f"Pipedrive API error: {result.get('error', 'Unknown error')}")
        except Exception as e:
            logger.error(f"Error creating organization: {str(e)}")
            raise Exception(f"Failed to create organization: {str(e)}")

    def create_person(self, data: Dict[str, Any], org_id: int) -> Dict[str, Any]:
        endpoint = f"{self.base_url}/persons"
        params = {'api_token': self.api_key}

        person_data = {
            'name': f"{data.get('AKP_VORNAME', '')} {data.get('AKP_NAME', '')}".strip(),
            'org_id': org_id,
            'email': [{'value': data.get('AKP_MAIL', ''), 'primary': True}] if data.get('AKP_MAIL') else [],
            'phone': [{'value': data.get('AKP_TEL', ''), 'primary': True}] if data.get('AKP_TEL') else [],
            'anredetext': data.get('ANR_ANREDETEXT', '')
        }

        # Add mapped custom fields from field mappings
        for mapping in self.field_mappings:
            if mapping['entity'] == 'person' and mapping['source'] in data:
                person_data[mapping['target']] = data[mapping['source']]

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

        deal_data = {
            'title': data.get('NPO_ProjName', ''),
            'org_id': org_id,
            'value': data.get('NPO_KSumme', 0),
            'currency': 'CHF',
            'pipeline_id': self.default_pipeline_id,
            'add_time': self._format_timestamp(data.get('NPO_KDatum')),
            'close_time': self._format_timestamp(data.get('NPO_ADatum'))
        }

        if deal_date < two_years_ago:
            deal_data.update({
                'status': 'lost',
                'lost_reason': 'Aged out',
                'lost_time': '2025-01-01'
            })
        else:
            deal_data['status'] = 'open'

        # Add mapped custom fields from field mappings
        for mapping in self.field_mappings:
            if mapping['entity'] == 'deal' and mapping['source'] in data:
                deal_data[mapping['target']] = data[mapping['source']]

        response = requests.post(endpoint, params=params, json=deal_data)
        return response.json()