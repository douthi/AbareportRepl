from flask import Flask, jsonify, request, render_template, send_file
from config import Config
from helpers import ReportManager
import logging
from datetime import datetime
import csv
import io
import tempfile

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Initialize report manager
report_manager = ReportManager(app.config)

@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html', 
                         config=app.config,
                         current_year=datetime.now().year,
                         data=[])  # Empty initial data

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


        if not mandant or mandant not in app.config['SUPPORTED_MANDANTS']:
            return jsonify({'error': 'Invalid mandant'}), 400

        report_ids = {}
        for report_key in app.config['REPORT_KEYS'].keys():
            try:
                report_id = report_manager.start_report(mandant, report_key, year)
                report_ids[report_key] = report_id
            except Exception as e:
                logger.error(f"Error starting report {report_key}: {e}")
                return jsonify({'error': f"Failed to start report {report_key}: {str(e)}"}), 500

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