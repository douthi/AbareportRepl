import json
import os
from dataclasses import dataclass, asdict
from flask import Blueprint, render_template, jsonify, request, flash, redirect, url_for
from pipedrive_helper import PipedriveHelper
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('pipedrive_config', __name__)

@dataclass
class SyncSettings:
    check_organizations: bool = True
    check_persons: bool = True
    sequential_status: bool = True
    set_won_time: bool = True
    set_lost_time: bool = True

AVAILABLE_COMPANIES = ['uniska', 'novisol']

class PipedriveConfig:
    def __init__(self, company_key='uniska'):
        if company_key not in AVAILABLE_COMPANIES:
            raise ValueError(f"Invalid company key. Must be one of: {AVAILABLE_COMPANIES}")

        self.company_key = company_key
        self.mapping_file = f'mappings/{company_key}_field_mappings.json'
        self.settings_file = f'mappings/{company_key}_sync_settings.json'

        # Create mappings directory if it doesn't exist
        os.makedirs('mappings', exist_ok=True)
        logger.debug(f"Initializing PipedriveConfig for company: {company_key}")
        logger.debug(f"Mapping file path: {self.mapping_file}")

        self._load_settings()
        self._load_mappings()

    def _load_settings(self):
        """Load sync settings from file."""
        try:
            with open(self.settings_file, 'r') as f:
                settings_dict = json.load(f)
                self.settings = SyncSettings(**settings_dict)
        except (FileNotFoundError, json.JSONDecodeError):
            self.settings = SyncSettings()
            self._save_settings()

    def _save_settings(self):
        """Save sync settings to file."""
        with open(self.settings_file, 'w') as f:
            json.dump(asdict(self.settings), f)

    def _load_mappings(self):
        """Load field mappings from file."""
        try:
            with open(self.mapping_file, 'r') as f:
                self.mappings = json.load(f)
                logger.debug(f"Loaded {len(self.mappings)} mappings for company {self.company_key}")
        except FileNotFoundError:
            logger.debug(f"No existing mappings file found for {self.company_key}, creating new")
            self.mappings = []
            self._save_mappings()
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding mappings file for {self.company_key}: {e}")
            self.mappings = []
            self._save_mappings()

    def _save_mappings(self):
        """Save field mappings to file."""
        try:
            with open(self.mapping_file, 'w') as f:
                json.dump(self.mappings, f, indent=2)
            logger.debug(f"Saved {len(self.mappings)} mappings for company {self.company_key}")
        except Exception as e:
            logger.error(f"Error saving mappings for {self.company_key}: {e}")
            raise

    def get_mappings_by_entity(self, entity_type):
        """Get field mappings for a specific entity type."""
        mappings = [m for m in self.mappings if m['entity'] == entity_type]
        logger.debug(f"Retrieved {len(mappings)} mappings for entity {entity_type} in company {self.company_key}")
        return mappings

    def add_mapping(self, mapping_data):
        """Add a new field mapping."""
        try:
            mapping = {
                'source': mapping_data['source'],
                'target': mapping_data['target'],
                'entity': mapping_data['entity']
            }
            # Check for duplicates
            for existing in self.mappings:
                if (existing['source'] == mapping['source'] and 
                    existing['entity'] == mapping['entity']):
                    return False, "Source field already mapped"

            self.mappings.append(mapping)
            self._save_mappings()
            return True, "Mapping added successfully"
        except KeyError as e:
            logger.error(f"Invalid mapping data: {e}")
            return False, f"Missing required field: {e}"
        except Exception as e:
            logger.error(f"Error adding mapping: {e}")
            return False, str(e)

    def update_mapping(self, mapping_id, mapping_data):
        """Update an existing field mapping."""
        if 0 <= mapping_id < len(self.mappings):
            try:
                # Check for duplicates excluding current mapping
                for i, existing in enumerate(self.mappings):
                    if i != mapping_id and (
                        existing['source'] == mapping_data['source'] and 
                        existing['entity'] == mapping_data['entity']
                    ):
                        return False, "Source field already mapped"

                self.mappings[mapping_id].update(mapping_data)
                self._save_mappings()
                return True, "Mapping updated successfully"
            except Exception as e:
                logger.error(f"Error updating mapping: {e}")
                return False, str(e)
        return False, "Invalid mapping ID"

    def delete_mapping(self, mapping_id):
        """Delete a field mapping."""
        if 0 <= mapping_id < len(self.mappings):
            try:
                self.mappings.pop(mapping_id)
                self._save_mappings()
                return True, "Mapping deleted successfully"
            except Exception as e:
                logger.error(f"Error deleting mapping: {e}")
                return False, str(e)
        return False, "Invalid mapping ID"

    def update_settings(self, settings_data):
        """Update sync settings."""
        try:
            self.settings = SyncSettings(**settings_data)
            self._save_settings()
            return True, "Settings updated successfully"
        except Exception as e:
            logger.error(f"Error updating settings: {e}")
            return False, str(e)

# Initialize configs for both companies
configs = {company: PipedriveConfig(company) for company in AVAILABLE_COMPANIES}

@bp.route('/wizard')
def show_wizard():
    """Show the Pipedrive mapping wizard."""
    try:
        company = request.args.get('company', 'uniska')
        if company not in AVAILABLE_COMPANIES:
            flash("Invalid company selected", "error")
            return redirect(url_for('index'))

        return render_template('pipedrive_mapping_wizard.html', 
                             companies=AVAILABLE_COMPANIES,
                             current_company=company)
    except Exception as e:
        logger.error(f"Error showing wizard: {e}")
        flash("Error loading wizard", "error")
        return redirect(url_for('index'))

@bp.route('/wizard/step/<entity_type>')
def get_wizard_step(entity_type):
    """Get the content for a wizard step."""
    try:
        if entity_type not in ['organization', 'person', 'deal', 'settings']:
            return jsonify({'error': 'Invalid entity type'}), 400

        company = request.args.get('company', 'uniska')
        if company not in AVAILABLE_COMPANIES:
            return jsonify({'error': 'Invalid company'}), 400

        return render_template(f'wizard_steps/{entity_type}.html')
    except Exception as e:
        logger.error(f"Error loading wizard step: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/wizard/finish', methods=['POST'])
def finish_wizard():
    """Save all mappings and settings from the wizard."""
    try:
        company = request.args.get('company', 'uniska')
        if company not in AVAILABLE_COMPANIES:
            return jsonify({'error': 'Invalid company'}), 400

        mappings = request.json
        if not mappings:
            return jsonify({'error': 'No mappings provided'}), 400

        config = configs[company]
        # Save mappings for each entity type
        for entity_type, entity_mappings in mappings.items():
            if entity_type == 'settings':
                continue  # Handle settings separately

            for mapping in entity_mappings:
                success, message = config.add_mapping({
                    'entity': entity_type,
                    'source': mapping['source'],
                    'target': mapping['target']
                })
                if not success:
                    return jsonify({'error': f'Error saving {entity_type} mapping: {message}'}), 500

        flash('Field mappings saved successfully', 'success')
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error finishing wizard: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/config')
def show_config():
    """Show the Pipedrive configuration page."""
    try:
        company = request.args.get('company', 'uniska')
        if company not in AVAILABLE_COMPANIES:
            flash("Invalid company selected", "error")
            return redirect(url_for('index'))

        config = configs[company]
        return render_template('pipedrive_config.html',
                                 organization_mappings=config.get_mappings_by_entity('organization'),
                                 person_mappings=config.get_mappings_by_entity('person'),
                                 deal_mappings=config.get_mappings_by_entity('deal'),
                                 settings=config.settings,
                                 company=company)
    except Exception as e:
        logger.error(f"Error rendering config page: {e}")
        flash("Error loading configuration", "error")
        return redirect(url_for('index'))

@bp.route('/api/refresh_fields/<entity_type>')
def refresh_fields(entity_type):
    """Refresh available fields from Pipedrive."""
    try:
        company = request.args.get('company', 'uniska')
        if company not in AVAILABLE_COMPANIES:
            return jsonify({'error': 'Invalid company'}), 400

        pipedrive = PipedriveHelper(company_key=company)

        if entity_type == 'organization':
            fields = pipedrive.get_organization_fields()
        elif entity_type == 'person':
            fields = pipedrive.get_person_fields()
        elif entity_type == 'deal':
            fields = pipedrive.get_deal_fields()
        else:
            return jsonify({'success': False, 'error': 'Invalid entity type'})

        logger.debug(f"Retrieved {len(fields)} fields for {entity_type}")
        return jsonify({'success': True, 'fields': fields})
    except Exception as e:
        logger.error(f"Error refreshing fields: {e}")
        return jsonify({'success': False, 'error': str(e)})

@bp.route('/api/available_fields/<entity_type>')
def get_available_fields(entity_type):
    """Get available fields for an entity type."""
    try:
        company = request.args.get('company', 'uniska')
        if company not in AVAILABLE_COMPANIES:
            return jsonify({'error': 'Invalid company'}), 400

        pipedrive = PipedriveHelper(company_key=company)

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
        logger.error(f"Error getting available fields: {e}")
        return jsonify({'success': False, 'error': str(e)})


@bp.route('/api/mapping', methods=['POST'])
def add_mapping():
    """Add a new field mapping."""
    try:
        company = request.args.get('company', 'uniska')
        if company not in AVAILABLE_COMPANIES:
            return jsonify({'error': 'Invalid company'}), 400

        config = configs[company]
        mapping_data = request.json
        success, message = config.add_mapping(mapping_data)
        if success:
            flash('Mapping added successfully', 'success')
            return jsonify({'success': True, 'message': message})
        return jsonify({'success': False, 'error': message})
    except Exception as e:
        logger.error(f"Error adding mapping: {e}")
        return jsonify({'success': False, 'error': str(e)})

@bp.route('/api/mapping/<entity_type>/<int:mapping_id>', methods=['GET', 'PUT', 'DELETE'])
def manage_mapping(entity_type, mapping_id):
    """Manage (get/update/delete) a field mapping."""
    try:
        company = request.args.get('company', 'uniska')
        if company not in AVAILABLE_COMPANIES:
            return jsonify({'error': 'Invalid company'}), 400

        config = configs[company]

        if request.method == 'GET':
            mappings = config.get_mappings_by_entity(entity_type)
            if 0 <= mapping_id < len(mappings):
                return jsonify({'success': True, 'mapping': mappings[mapping_id]})
            return jsonify({'success': False, 'error': 'Mapping not found'})

        elif request.method == 'PUT':
            success, message = config.update_mapping(mapping_id, request.json)
            if success:
                flash('Mapping updated successfully', 'success')
                return jsonify({'success': True, 'message': message})
            return jsonify({'success': False, 'error': message})

        elif request.method == 'DELETE':
            success, message = config.delete_mapping(mapping_id)
            if success:
                flash('Mapping deleted successfully', 'success')
                return jsonify({'success': True, 'message': message})
            return jsonify({'success': False, 'error': message})

    except Exception as e:
        logger.error(f"Error managing mapping: {e}")
        return jsonify({'success': False, 'error': str(e)})

@bp.route('/api/sync_settings', methods=['POST'])
def save_sync_settings():
    """Save synchronization settings."""
    try:
        company = request.args.get('company', 'uniska')
        if company not in AVAILABLE_COMPANIES:
            return jsonify({'error': 'Invalid company'}), 400
        config = configs[company]
        settings_data = request.json
        success, message = config.update_settings(settings_data)
        if success:
            flash('Settings saved successfully', 'success')
            return jsonify({'success': True, 'message': message})
        return jsonify({'success': False, 'error': message})
    except Exception as e:
        logger.error(f"Error saving sync settings: {e}")
        return jsonify({'success': False, 'error': str(e)})

@bp.route('/api/mappings/<entity_type>', methods=['GET'])
def get_mappings(entity_type):
    """Get all field mappings for a specific entity type."""
    try:
        company = request.args.get('company', 'uniska')
        if company not in AVAILABLE_COMPANIES:
            return jsonify({'error': 'Invalid company'}), 400

        logger.debug(f"Getting mappings for company: {company}, entity: {entity_type}")
        config = configs[company]
        mappings = config.get_mappings_by_entity(entity_type)
        logger.debug(f"Retrieved {len(mappings)} mappings")
        return jsonify({'success': True, 'mappings': mappings})
    except Exception as e:
        logger.error(f"Error getting mappings: {e}")
        return jsonify({'success': False, 'error': str(e)})