import pytest
from routes.pipedrive_config import PipedriveConfig

def test_pipedrive_config_initialization():
    """Test PipedriveConfig initialization."""
    config = PipedriveConfig(company_key='test_company')
    assert config.company_key == 'test_company'
    assert config.mapping_file == 'mappings/test_company_field_mappings.json'
    assert config.settings_file == 'mappings/test_company_sync_settings.json'

def test_add_mapping():
    """Test adding a new field mapping."""
    config = PipedriveConfig(company_key='test_company')
    
    # Test adding a valid mapping
    success, message = config.add_mapping({
        'source': 'ADR_NAME',
        'target': 'name',
        'entity': 'organization'
    })
    assert success is True
    assert 'successfully' in message.lower()
    
    # Test adding a duplicate mapping
    success, message = config.add_mapping({
        'source': 'ADR_NAME',
        'target': 'different_field',
        'entity': 'organization'
    })
    assert success is False
    assert 'already mapped' in message.lower()

def test_update_settings():
    """Test updating sync settings."""
    config = PipedriveConfig(company_key='test_company')
    
    success, message = config.update_settings({
        'check_organizations': True,
        'check_persons': True,
        'sequential_status': True,
        'set_won_time': True,
        'set_lost_time': True
    })
    assert success is True
    assert 'successfully' in message.lower()

@pytest.mark.parametrize('entity_type', ['organization', 'person', 'deal'])
def test_get_mappings_by_entity(entity_type):
    """Test getting mappings for specific entity types."""
    config = PipedriveConfig(company_key='test_company')
    
    # Add a test mapping
    config.add_mapping({
        'source': f'test_source_{entity_type}',
        'target': 'test_target',
        'entity': entity_type
    })
    
    mappings = config.get_mappings_by_entity(entity_type)
    assert len(mappings) > 0
    assert mappings[0]['entity'] == entity_type
