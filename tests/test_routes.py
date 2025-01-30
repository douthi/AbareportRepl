import json
import pytest
from flask import url_for

def test_wizard_endpoint(client):
    """Test the Pipedrive mapping wizard endpoint."""
    response = client.get('/wizard')
    assert response.status_code == 200
    assert b'Pipedrive Field Mapping Wizard' in response.data

def test_wizard_steps(client):
    """Test the wizard step endpoints."""
    entity_types = ['organization', 'person', 'deal', 'settings']

    for entity_type in entity_types:
        response = client.get(f'/wizard/step/{entity_type}')
        assert response.status_code == 200

    # Test invalid entity type
    response = client.get('/wizard/step/invalid')
    assert response.status_code == 400

def test_field_mapping_api(client):
    """Test field mapping API endpoints."""
    # Test adding a new mapping
    mapping_data = {
        'entity': 'organization',
        'source': 'ADR_NAME',
        'target': 'name'
    }

    response = client.post('/api/mapping',
                          data=json.dumps(mapping_data),
                          content_type='application/json')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True

    # Test getting available fields
    response = client.get('/api/available_fields/organization')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'fields' in data

def test_sync_settings_api(client):
    """Test sync settings API endpoint."""
    settings_data = {
        'check_organizations': True,
        'check_persons': True,
        'sequential_status': True,
        'set_won_time': True,
        'set_lost_time': True
    }

    response = client.post('/api/sync_settings',
                          data=json.dumps(settings_data),
                          content_type='application/json')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True