
import os
import json
import requests
from typing import Dict, Any, List

class PipedriveHelper:
    def __init__(self):
        self.api_key = os.getenv('PIPEDRIVE_API_KEY')
        self.base_url = 'https://api.pipedrive.com/v1'
        self.mapping_file = 'pipedrive_mappings.json'
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

    def create_deal(self, data: Dict[str, Any], org_id: int) -> Dict[str, Any]:
        endpoint = f"{self.base_url}/deals"
        params = {'api_token': self.api_key}
        
        deal_data = {
            'title': data['ProjName'],
            'org_id': org_id,
            'value': data['KSumme'],
            'currency': 'CHF'
        }
        
        response = requests.post(endpoint, params=params, json=deal_data)
        return response.json()
