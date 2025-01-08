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

        # Define friendly names for Pipedrive fields
        self.field_friendly_names = {
            # Organization fields
            'name': 'Company Name',
            'address': 'Street Address',
            'address_postal_code': 'Postal Code',
            'address_city': 'City',
            'address_country': 'Country',
            'website': 'Website URL',
            'industry': 'Industry',

            # Person fields
            'email': 'Email Address',
            'phone': 'Phone Number',
            'name': 'Contact Name',
            'org_id': 'Organization',
            'position': 'Job Title',

            # Deal fields
            'title': 'Deal Title',
            'value': 'Deal Value',
            'currency': 'Currency',
            'status': 'Deal Status',
            'expected_close_date': 'Expected Close Date',
            'probability': 'Win Probability',

            # Custom fields are handled dynamically
            'custom_fields': 'Custom Fields'
        }

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

    def get_available_fields(self):
        """Get available Pipedrive fields with friendly names."""
        try:
            # Fetch organization fields
            org_fields = self._get_fields('organizationFields')
            person_fields = self._get_fields('personFields')
            deal_fields = self._get_fields('dealFields')

            fields = {
                'organization': self._format_fields(org_fields),
                'person': self._format_fields(person_fields),
                'deal': self._format_fields(deal_fields)
            }

            return fields
        except Exception as e:
            return {
                'organization': self.field_friendly_names,
                'person': self.field_friendly_names,
                'deal': self.field_friendly_names
            }

    def _get_fields(self, endpoint):
        """Fetch fields from Pipedrive API."""
        if not self.api_key:
            return {}

        response = requests.get(
            f"{self.base_url}/{endpoint}",
            params={'api_token': self.api_key}
        )
        if response.ok:
            return response.json().get('data', [])
        return []

    def _format_fields(self, fields):
        """Format API fields with friendly names."""
        formatted = {}
        for field in fields:
            key = field.get('key')
            name = field.get('name')
            if key and name:
                formatted[key] = name
        return formatted

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