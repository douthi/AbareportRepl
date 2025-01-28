from flask import Flask, jsonify, request, render_template, send_file, redirect, url_for
import os
from config import Config
from helpers import ReportManager
from pipedrive_helper import PipedriveHelper
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

# Initialize managers
report_manager = ReportManager(app.config)

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

@app.route('/<company_name>/config', methods=['GET', 'POST'])
def company_config(company_name):
    """Render company configuration page."""
    if company_name not in ['uniska', 'novisol']:
        return redirect(url_for('company_dashboard', company_name='uniska'))
        
    if request.method == 'POST':
        data = request.get_json()
        if 'pipedrive_key' in data:
            # Update Pipedrive API key in environment
            os.environ[f'{company_name.upper()}_PIPEDRIVE_API_KEY'] = data['pipedrive_key']
            app.config['COMPANIES'][company_name]['pipedrive_api_key'] = data['pipedrive_key']
            return jsonify({'status': 'success'})
        return jsonify({'error': 'Invalid data'}), 400
        
    return render_template('company_config.html', company=company_name, config=app.config)

@app.route('/<company_name>/field-mappings', methods=['GET', 'POST'])
def field_mappings(company_name):
    """Handle company field mappings."""
    if company_name not in ['uniska', 'novisol']:
        return jsonify({'error': 'Invalid company'}), 400
        
    pipedrive_helper = PipedriveHelper(company_name)
    
    if request.method == 'POST':
        mappings = request.get_json()
        pipedrive_helper.save_field_mappings(mappings)
        return jsonify({'status': 'success'})
        
    return jsonify(pipedrive_helper.get_field_mappings())

@app.route('/<company_name>/mapping')
def company_mapping(company_name):
    """Render company field mapping page."""
    if company_name not in ['uniska', 'novisol']:
        return redirect(url_for('company_dashboard', company_name='uniska'))
    return render_template('field_mapping.html', company=company_name)

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

        # Define custom column headers and order
        columns = [
            'ProjNr', 'ProjName', 'NAME', 'VORNAME', 'EMAIL', 'TEL',
            'LAND', 'PLZ', 'ORT', 'STREET', 'HOUSE_NUMBER',
            'KDatum', 'KSumme', 'ADatum', 'ASumme', 'Status'
        ]

        # Create a temporary file-like object
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=columns)

        # Write headers with custom formatting
        writer.writeheader()

        # Write data rows
        for row in data:
            # Create a filtered dictionary with only the specified columns
            filtered_row = {col: row.get(col, '') for col in columns}

            # Apply custom formatting
            if 'KSumme' in filtered_row:
                # Format currency values
                try:
                    value = float(filtered_row['KSumme'])
                    filtered_row['KSumme'] = f"CHF {value:,.2f}"
                except (ValueError, TypeError):
                    pass

            if 'ASumme' in filtered_row:
                try:
                    value = float(filtered_row['ASumme'])
                    filtered_row['ASumme'] = f"CHF {value:,.2f}"
                except (ValueError, TypeError):
                    pass

            # Format dates
            for date_field in ['KDatum', 'ADatum']:
                if filtered_row.get(date_field):
                    try:
                        date_obj = datetime.strptime(filtered_row[date_field], '%Y-%m-%d')
                        filtered_row[date_field] = date_obj.strftime('%d.%m.%Y')
                    except ValueError:
                        pass

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
        company_config = app.config['COMPANIES'].get(company, {})
        company_mandants = company_config.get('mandants', {})

        if not mandant or mandant not in company_mandants:
            return jsonify({'error': 'Invalid mandant'}), 400

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


@app.route('/sync', methods=['POST'])
def sync_to_pipedrive():
    """Sync a record to Pipedrive."""
    try:
        data = request.json
        company_key = data.pop('company_key', 'uniska')
        pipedrive_helper = PipedriveHelper(company_key)
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # Create organization
        org_result = pipedrive_helper.create_organization(data)
        if not org_result.get('success'):
            return jsonify({'error': 'Failed to create organization'}), 500

        org_id = org_result['data']['id']

        # Create person if name exists
        if data.get('VORNAME') or data.get('NAME'):
            person_result = pipedrive_helper.create_person(data, org_id)
            if not person_result.get('success'):
                return jsonify({'error': 'Failed to create person'}), 500

        # Create deal
        deal_result = pipedrive_helper.create_deal(data, org_id)
        if not deal_result.get('success'):
            return jsonify({'error': 'Failed to create deal'}), 500

        return jsonify({'success': True, 'message': 'Data synced to Pipedrive'}), 200

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