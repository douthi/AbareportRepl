from flask import Flask, jsonify, request, render_template, send_file, redirect, url_for
import os
from config import Config
from helpers import ReportManager
from pipedrive_helper import PipedriveHelper
from utils import RateLimiter
import logging
from datetime import datetime
import csv
import io

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Global error handler
@app.errorhandler(Exception)
def handle_error(error):
    logger.error(f"Unhandled error: {error}")
    return jsonify({'error': str(error)}), 500

# Rate limiting
limiter = RateLimiter()
@app.before_request
def check_rate_limit():
    if not limiter.can_make_request(
        request.headers.get('X-Replit-User-Id', 'anonymous'),
        request.endpoint
    ):
        return jsonify({'error': 'Rate limit exceeded'}), 429

# Initialize managers
report_manager = ReportManager(app.config)

# Simulate a key-value store (replace with a real database in production)
db = {}

@app.route('/')
def index():
    """Redirect to Uniska page by default."""
    return redirect(url_for('company_dashboard', company_name='uniska'))

@app.route('/<company_name>')
def company_dashboard(company_name):
    """Render company dashboard."""
    if company_name not in ['uniska', 'novisol']:
        return redirect(url_for('company_dashboard', company_name='uniska'))
    return render_template('index.html', company=company_name, config=app.config, current_year=datetime.now().year, data=[])





@app.route('/pipedrive-fields', methods=['GET'])
def get_pipedrive_fields():
    """Get all available Pipedrive fields."""
    try:
        company_key = request.args.get('company', 'uniska')
        pipedrive = PipedriveHelper(company_key)

        fields = {
            'organization': pipedrive.get_organization_fields(),
            'person': pipedrive.get_person_fields(),
            'deal': pipedrive.get_deal_fields()
        }

        return jsonify(fields)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/pipedrive-config', methods=['GET', 'POST'])
def pipedrive_config():
    """Handle Pipedrive field mapping configuration."""
    if request.method == 'GET':
        if request.headers.get('Accept') == 'application/json':
            return jsonify(pipedrive_helper.get_field_mappings())
        return render_template('config.html')

    if request.method == 'POST':
        mappings = request.json
        pipedrive_helper.save_field_mappings(mappings)
        return jsonify({'status': 'success'})

@app.route('/export', methods=['GET'])
def export_data():
    """Export combined data in CSV format with custom formatting."""
    try:
        data = report_manager.get_combined_data()

        if not data:
            return jsonify({'error': 'No data available to export'}), 404

        # Define specific columns to export
        columns = [
            # AKP columns
            'AKP_INR', 'AKP_NR', 'AKP_NAME', 'AKP_VORNAME', 'AKP_FUNKTION', 'AKP_SUBJEKT_NR',
            'AKP_ANR_NR', 'AKP_ANREDENAME', 'AKP_TEL', 'AKP_MAIL', 'AKP_WWW', 'AKP_TEL2',
            'AKP_TEL3', 'AKP_TEL4', 'AKP_ABTEILUNG', 'AKP_ANR_GROUP',
            # ANR columns
            'ANR_ANREDE', 'ANR_ANREDETEXT',
            # ADR columns
            'ADR_INR', 'ADR_KURZNA', 'ADR_LAND', 'ADR_PLZ', 'ADR_NAME', 'ADR_VORNAME',
            'ADR_ORT', 'ADR_EMAIL', 'ADR_STAAT', 'ADR_STREET', 'ADR_TEL', 'ADR_TEL2',
            'ADR_TELEX', 'ADR_TELEFAX', 'ADR_SPRACHE', 'ADR_WWW', 'ADR_HOUSE_NUMBER',
            'ADR_PostOfficeBoxText', 'ADR_PostOfficeBoxNumber', 'ADR_ANR_GROUP',
            # NPO columns
            'NPO_ProjNr', 'NPO_ProjName', 'NPO_Status', 'NPO_Status1', 'NPO_Status2',
            'NPO_Status3', 'NPO_Status4', 'NPO_KDatum', 'NPO_KSumme', 'NPO_ADatum', 'NPO_ASumme'
        ]

        # Create a temporary file-like object
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=columns)

        # Write headers
        writer.writeheader()

        # Write data rows, only including specified columns
        for row in data:
            filtered_row = {col: row.get(col, '') for col in columns}
            writer.writerow(filtered_row)

        # Prepare the output
        output.seek(0)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8-sig')),  # Use UTF-8 with BOM for Excel compatibility
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'crm_sync_export_{timestamp}.csv'
        )

    except Exception as e:
        logger.error(f"Error exporting data: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/startAllReports', methods=['POST'])
def start_all_reports():
    """Start all reports for a given mandant and year."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400

        mandant = data.get('mandant')
        year = data.get('year', 'none')
        report_key = data.get('report_key')


        # Get company from request
        company = data.get('company', 'uniska')
        logger.debug(f"Received request for company: {company}")
        company_config = app.config['COMPANIES'].get(company, {})
        company_mandants = company_config.get('mandants', {})

        logger.debug(f"Company: {company}")
        logger.debug(f"Mandant: {mandant}")
        logger.debug(f"Available mandants: {company_mandants}")

        if not mandant:
            return jsonify({'error': 'No mandant provided'}), 400
            
        if mandant not in company_mandants:
            return jsonify({'error': f'Invalid mandant {mandant}. Available mandants: {company_mandants}'}), 400

        report_ids = {}
        company_config = app.config['COMPANIES'][company]
        report_keys = company_config.get('report_keys', {})

        for report_key in report_keys.keys():
            try:
                logger.info(f"Starting report {report_key} for mandant {mandant}")
                report_id = report_manager.start_report(mandant, report_key, year)
                report_ids[report_key] = report_id
                logger.info(f"Successfully started report {report_key} with ID {report_id}")
            except Exception as e:
                error_msg = f"Failed to start report {report_key} for mandant {mandant}: {str(e)}"
                logger.error(error_msg)
                return jsonify({'error': error_msg}), 500

        return jsonify({'report_ids': report_ids}), 200

    except Exception as e:
        logger.error(f"Error in start_all_reports: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/reports', methods=['GET'])
def get_reports():
    """Get status of all reports."""
    try:
        reports = report_manager.get_all_reports()
        return jsonify({'reports': reports}), 200
    except Exception as e:
        logger.error(f"Error getting reports: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/sync-to-pipedrive', methods=['POST'])
def sync_to_pipedrive():
    """Sync a record to Pipedrive."""
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data received'}), 400

        proj_nr = data.get('ProjNr')
        company_key = data.pop('company_key', 'uniska')

        # Save sync status
        if proj_nr:
            sync_key = f"{company_key}_synced_entries"
            if sync_key not in db:
                db[sync_key] = []
            synced_entries = db[sync_key]
            if proj_nr not in synced_entries:
                synced_entries.append(proj_nr)
                db[sync_key] = synced_entries

        if not os.getenv(f'{company_key.upper()}_PIPEDRIVE_API_KEY'):
            return jsonify({'error': 'Pipedrive API key not configured'}), 400

        pipedrive = PipedriveHelper(company_key)

        # Create or update organization
        org_name = data.get('ADR_NAME')
        if not org_name:
            return jsonify({'error': 'Organization name (ADR_NAME) is required'}), 400

        existing_org = pipedrive.find_organization_by_name(org_name)
        if existing_org:
            logger.info(f"Found existing organization: {existing_org['name']}")
            org_id = existing_org['id']
            org_result = pipedrive.update_organization(org_id, data)
        else:
            logger.info(f"Creating new organization: {org_name}")
            org_result = pipedrive.create_organization(data)
            if not org_result.get('success'):
                logger.error(f"Failed to create organization: {org_result}")
                return jsonify({'error': org_result.get('error', 'Failed to create organization')}), 500
            org_id = org_result['data']['id']
            logger.info(f"Created organization with ID: {org_id}")

        # Create or update person with complete data
        person_name = f"{data.get('AKP_VORNAME', '')} {data.get('AKP_NAME', '')}".strip()
        if person_name:
            logger.info(f"Processing person: {person_name}")
            existing_person = pipedrive.find_person_by_name(person_name, org_id)
            if existing_person:
                logger.info(f"Found existing person: {existing_person['name']}")
                person_result = pipedrive.update_person(existing_person['id'], data)
            else:
                logger.info(f"Creating new person: {person_name}")
                person_result = pipedrive.create_person(data, org_id)
                if not person_result.get('success'):
                    logger.error(f"Failed to create person: {person_result}")
                    return jsonify({'error': person_result.get('error', 'Failed to create person')}), 500
                logger.info(f"Created person with ID: {person_result['data']['id']}")

        # Create deal with all related data if it doesn't exist
        logger.info("Creating deal...")
        deal_result = pipedrive.create_deal(data, org_id)
        if not deal_result.get('success'):
            error_msg = deal_result.get('error', '')
            if error_msg == 'Deal already exists':
                return jsonify({'message': 'Deal already exists, skipping'}), 200
            logger.error(f"Failed to create deal: {deal_result}")
            return jsonify({'error': error_msg}), 500
        logger.info(f"Created deal with ID: {deal_result['data']['id']}")

        return jsonify({'success': True, 'message': 'Record synced successfully'}), 200

    except Exception as e:
        logger.error(f"Error syncing to Pipedrive: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/reportData/<report_id>', methods=['GET'])
def get_report_data(report_id):
    """Get data for a specific report."""
    try:
        status = report_manager.get_report_status(report_id)
        if not status:
            return jsonify({'error': 'Report not found'}), 404

        if status['status'] != 'FinishedSuccess':
            return jsonify({'error': 'Report data not available', 'status': status['status']}), 404

        data = report_manager.get_report_data(report_id)
        if not data:
            return jsonify({'error': 'Report data not found'}), 404

        return jsonify({'report_data': data}), 200

    except Exception as e:
        logger.error(f"Error getting report data: {e}")
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def not_found_error(error):
    return jsonify({'error': 'Not found'}), 404

@app.route('/combinedData', methods=['GET', 'POST'])
def get_combined_data():
    """Get combined and matched data from all reports."""
    try:
        data = report_manager.get_combined_data()

        # Check if HTML format is requested
        if request.args.get('format') == 'html':
            if not data:
                return '<p>No data available</p>'

            # Start HTML table
            html = '<table border="1" style="border-collapse: collapse; width: 100%;">'

            # Headers
            if data:
                headers = list(data[0].keys())
                html += '<tr>'
                for header in headers:
                    html += f'<th style="padding: 8px; text-align: left;">{header}</th>'
                html += '</tr>'

            # Data rows
            for row in data:
                html += '<tr>'
                for header in headers:
                    value = row.get(header, '')
                    html += f'<td style="padding: 8px;">{value}</td>'
                html += '</tr>'

            html += '</table>'
            return html

        return jsonify({'combined_data': data}), 200
    except Exception as e:
        logger.error(f"Error getting combined data: {e}")
        return jsonify({'error': str(e)}), 500

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({'error': 'Internal server error'}), 500