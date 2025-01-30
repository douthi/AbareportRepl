import json
import os
from dataclasses import dataclass, asdict
from flask import Blueprint, render_template, jsonify, request, flash, redirect, url_for
from pipedrive_helper import PipedriveHelper

bp = Blueprint('pipedrive_config', __name__)

@dataclass
class SyncSettings:
    check_organizations: bool = True
    check_persons: bool = True
    sequential_status: bool = True

class PipedriveConfig:
    def __init__(self, company_key='uniska'):
        self.company_key = company_key
        self.mapping_file = f'mappings/{company_key}_field_mappings.json'
        self.settings_file = f'mappings/{company_key}_sync_settings.json'
        os.makedirs('mappings', exist_ok=True)
        self._load_settings()
        self._load_mappings()

    def _load_settings(self):
        try:
            with open(self.settings_file, 'r') as f:
                settings_dict = json.load(f)
                self.settings = SyncSettings(**settings_dict)
        except (FileNotFoundError, json.JSONDecodeError):
            self.settings = SyncSettings()
            self._save_settings()

    def _save_settings(self):
        with open(self.settings_file, 'w') as f:
            json.dump(asdict(self.settings), f)

    def _load_mappings(self):
        try:
            with open(self.mapping_file, 'r') as f:
                self.mappings = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.mappings = []
            self._save_mappings()

    def _save_mappings(self):
        with open(self.mapping_file, 'w') as f:
            json.dump(self.mappings, f, indent=2)

    def get_mappings_by_entity(self, entity_type):
        return [m for m in self.mappings if m['entity'] == entity_type]

    def add_mapping(self, mapping_data):
        mapping = {
            'source': mapping_data['source'],
            'target': mapping_data['target'],
            'entity': mapping_data['entity']
        }
        self.mappings.append(mapping)
        self._save_mappings()
        return True

    def update_mapping(self, mapping_id, mapping_data):
        if 0 <= mapping_id < len(self.mappings):
            self.mappings[mapping_id].update(mapping_data)
            self._save_mappings()
            return True
        return False

    def delete_mapping(self, mapping_id):
        if 0 <= mapping_id < len(self.mappings):
            self.mappings.pop(mapping_id)
            self._save_mappings()
            return True
        return False

    def update_settings(self, settings_data):
        self.settings = SyncSettings(**settings_data)
        self._save_settings()
        return True

config = PipedriveConfig()

@bp.route('/config')
def show_config():
    """Show the Pipedrive configuration page."""
    return render_template('pipedrive_config.html',
                         organization_mappings=config.get_mappings_by_entity('organization'),
                         person_mappings=config.get_mappings_by_entity('person'),
                         deal_mappings=config.get_mappings_by_entity('deal'),
                         settings=config.settings)

@bp.route('/api/refresh_fields/<entity_type>')
def refresh_fields(entity_type):
    """Refresh available fields from Pipedrive."""
    try:
        pipedrive = PipedriveHelper()

        if entity_type == 'organization':
            fields = pipedrive.get_organization_fields()
        elif entity_type == 'person':
            fields = pipedrive.get_person_fields()
        elif entity_type == 'deal':
            fields = pipedrive.get_deal_fields()
        else:
            return jsonify({'success': False, 'error': 'Invalid entity type'})

        return jsonify({'success': True, 'fields': fields})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@bp.route('/api/available_fields/<entity_type>')
def get_available_fields(entity_type):
    """Get available fields for an entity type."""
    try:
        pipedrive = PipedriveHelper()

        if entity_type == 'organization':
            fields = pipedrive.get_organization_fields()
        elif entity_type == 'person':
            fields = pipedrive.get_person_fields()
        elif entity_type == 'deal':
            fields = pipedrive.get_deal_fields()
        else:
            return jsonify({'success': False, 'error': 'Invalid entity type'})

        return jsonify({'success': True, 'fields': fields})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@bp.route('/api/mapping', methods=['POST'])
def add_mapping():
    """Add a new field mapping."""
    try:
        mapping_data = request.json
        success = config.add_mapping(mapping_data)
        if success:
            flash('Mapping added successfully', 'success')
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Failed to add mapping'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@bp.route('/api/mapping/<entity_type>/<int:mapping_id>', methods=['GET', 'PUT', 'DELETE'])
def manage_mapping(entity_type, mapping_id):
    """Manage (get/update/delete) a field mapping."""
    try:
        if request.method == 'GET':
            mappings = config.get_mappings_by_entity(entity_type)
            if 0 <= mapping_id < len(mappings):
                return jsonify({'success': True, 'mapping': mappings[mapping_id]})
            return jsonify({'success': False, 'error': 'Mapping not found'})

        elif request.method == 'PUT':
            success = config.update_mapping(mapping_id, request.json)
            if success:
                flash('Mapping updated successfully', 'success')
                return jsonify({'success': True})
            return jsonify({'success': False, 'error': 'Failed to update mapping'})

        elif request.method == 'DELETE':
            success = config.delete_mapping(mapping_id)
            if success:
                flash('Mapping deleted successfully', 'success')
                return jsonify({'success': True})
            return jsonify({'success': False, 'error': 'Failed to delete mapping'})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@bp.route('/api/sync_settings', methods=['POST'])
def save_sync_settings():
    """Save synchronization settings."""
    try:
        settings_data = request.json
        success = config.update_settings(settings_data)
        if success:
            flash('Settings saved successfully', 'success')
            return jsonify({'success': True})
        return jsonify({'success': False, 'error': 'Failed to save settings'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
