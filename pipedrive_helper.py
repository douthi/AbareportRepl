
import os
import json
import requests
from typing import Dict, Any, List

class PipedriveHelper:
    def __init__(self, company_key='uniska'):
        self.company_key = company_key
        self.api_key = os.getenv(f'{company_key.upper()}_PIPEDRIVE_API_KEY')
        self.base_url = 'https://api.pipedrive.com/v1'
        self.mapping_file = f'mappings/{company_key}_field_mappings.json'
        os.makedirs('mappings', exist_ok=True)
        self._load_field_mappings()

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
        
    def create_organization(self, data: Dict[str, Any]) -> Dict[str, Any]:
        endpoint = f"{self.base_url}/organizations"
        params = {'api_token': self.api_key}
        
        org_data = {
            'name': data['NAME'],
            'address': f"{data['STREET']} {data['HOUSE_NUMBER']}",
            'address_postal_code': data['PLZ'],
            'address_city': data['ORT'],
            'address_country': data['LAND']
        }
        
        response = requests.post(endpoint, params=params, json=org_data)
        return response.json()

    def create_person(self, data: Dict[str, Any], org_id: int) -> Dict[str, Any]:
        endpoint = f"{self.base_url}/persons"
        params = {'api_token': self.api_key}
        
        person_data = {
            'name': f"{data['VORNAME']} {data['NAME']}".strip(),
            'org_id': org_id,
            'email': [{'value': data['EMAIL'], 'primary': True}] if data['EMAIL'] else [],
            'phone': [{'value': data['TEL'], 'primary': True}] if data['TEL'] else []
        }
        
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

    def search_organization(self, name: str) -> Optional[Dict[str, Any]]:
        """Search for organization by name."""
        endpoint = f"{self.base_url}/organizations/search"
        params = {
            'api_token': self.api_key,
            'term': name,
            'exact_match': True
        }
        response = requests.get(endpoint, params=params)
        data = response.json()
        if data.get('success') and data.get('data') and data['data'].get('items'):
            return data['data']['items'][0]['item']
        return None

    def search_person(self, name: str, org_id: int) -> Optional[Dict[str, Any]]:
        """Search for person by name and organization."""
        endpoint = f"{self.base_url}/persons/search"
        params = {
            'api_token': self.api_key,
            'term': name,
            'organization_id': org_id
        }
        response = requests.get(endpoint, params=params)
        data = response.json()
        if data.get('success') and data.get('data') and data['data'].get('items'):
            return data['data']['items'][0]['item']
        return None

    def search_deal(self, title: str, org_id: int) -> Optional[Dict[str, Any]]:
        """Search for deal by title and organization."""
        endpoint = f"{self.base_url}/deals/search"
        params = {
            'api_token': self.api_key,
            'term': title,
            'organization_id': org_id
        }
        response = requests.get(endpoint, params=params)
        data = response.json()
        if data.get('success') and data.get('data') and data['data'].get('items'):
            return data['data']['items'][0]['item']
        return None

    def create_deal(self, data: Dict[str, Any], org_id: int) -> Dict[str, Any]:
        endpoint = f"{self.base_url}/deals"
        params = {'api_token': self.api_key}
        
        deal_data = {
            'title': data['ProjName'],
            'org_id': org_id,
            'value': data.get('KSumme', 0),
            'currency': 'CHF',
            'status': 'open',
            'probability': data.get('probability', None),
            'expected_close_date': data.get('expected_close_date', None),
            'pipeline_id': data.get('pipeline_id', None),
            'stage_id': data.get('stage_id', None)
        }
        
        # Add mapped custom fields from field mappings
        for mapping in self.field_mappings:
            if mapping['entity'] == 'deal' and mapping['source'] in data:
                deal_data[mapping['target']] = data[mapping['source']]
        
        response = requests.post(endpoint, params=params, json=deal_data)
        return response.json()
