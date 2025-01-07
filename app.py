from flask import Flask, jsonify, request
from config import Config
from helpers import ReportManager
import logging

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
    """Root endpoint to verify API is working."""
    return jsonify({
        'status': 'ok',
        'message': 'API is running',
        'endpoints': {
            'POST /startAllReports': 'Start reports for a mandant',
            'GET /reports': 'Get all report statuses',
            'GET /reportData/<report_id>': 'Get specific report data'
        }
    })

@app.route('/startAllReports', methods=['POST'])
def start_all_reports():
    """Start all reports for a given mandant and year."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400

        mandant = data.get('mandant')
        year = data.get('year', 'none')

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

@app.route('/combinedData', methods=['GET'])
def get_combined_data():
    """Get combined and matched data from all reports."""
    try:
        data = report_manager.get_combined_data()
        return jsonify({'combined_data': data}), 200
    except Exception as e:
        logger.error(f"Error getting combined data: {e}")
        return jsonify({'error': str(e)}), 500

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({'error': 'Internal server error'}), 500
