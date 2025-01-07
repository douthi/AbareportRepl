import logging
import re
import time
import uuid
import threading
import requests
from typing import Dict, List, Any, Optional

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class ReportManager:
    def __init__(self, config):
        self.config = config
        self.report_status_store: Dict[str, Dict[str, Any]] = {}
        self.report_data_store: Dict[str, List[Dict[str, Any]]] = {}

    def get_access_token(self) -> str:
        """Get access token from Abacus ERP."""
        try:
            response = requests.post(
                self.config['TOKEN_URL'],
                data={
                    'grant_type': 'client_credentials',
                    'client_id': self.config['CLIENT_ID'],
                    'client_secret': self.config['CLIENT_SECRET']
                },
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            response.raise_for_status()
            access_token = response.json().get('access_token')
            logger.debug("Access token obtained successfully")
            return access_token
        except requests.exceptions.RequestException as e:
            logger.error(f"Error obtaining access token: {e}")
            raise

    def start_report(self, mandant: str, report_key: str, year: str) -> str:
        """Start a report and return the report ID."""
        access_token = self.get_access_token()
        report_id = str(uuid.uuid4())
        
        self.report_status_store[report_id] = {
            'mandant': mandant,
            'report_key': report_key,
            'api_report_id': None,
            'status': 'Running',
            'message': 'Report started.',
            'total_pages': 1
        }
        
        report_name = self.config.REPORT_KEYS.get(report_key)
        endpoint = f"/api/abareport/v1/report/{mandant}/{report_name}"
        
        # Build request body
        body = {
            "outputType": "json",
            "paging": self.config.PAGE_SIZE
        }
        
        # Add date parameters for dko report
        if report_key == "dko" and year != "none":
            body["parameters"] = {
                "AUF_DATUM_VON": f"{year}-01-01",
                "AUF_DATUM_BIS": f"{year}-12-31"
            }
        
        try:
            response = requests.post(
                f"{self.config.BASE_URL}{endpoint}",
                json=body,
                headers={
                    'Authorization': f'Bearer {access_token}',
                    'Content-Type': 'application/json'
                }
            )
            response.raise_for_status()
            api_report_id = response.json().get('id') or response.json().get('reportId')
            
            if not api_report_id:
                raise ValueError("API did not return a report ID")
            
            self.report_status_store[report_id]['api_report_id'] = api_report_id
            logger.info(f"Report '{report_key.upper()}' started with ID: {report_id}")
            
            # Start polling in background
            self._start_polling(report_id, api_report_id, report_key)
            
            return report_id
        except Exception as e:
            self.report_status_store[report_id]['status'] = 'FinishedError'
            self.report_status_store[report_id]['message'] = str(e)
            logger.error(f"Error starting report '{report_key.upper()}': {e}")
            raise

    def _start_polling(self, report_id: str, api_report_id: str, report_key: str) -> None:
        """Start polling for report status in a background thread."""
        def poll():
            while True:
                try:
                    access_token = self.get_access_token()
                    status_endpoint = f"/api/abareport/v1/jobs/{api_report_id}"
                    
                    response = requests.get(
                        f"{self.config.BASE_URL}{status_endpoint}",
                        headers={
                            'Authorization': f'Bearer {access_token}',
                            'Content-Type': 'application/json'
                        }
                    )
                    response.raise_for_status()
                    data = response.json()
                    
                    state = data.get('state')
                    message = data.get('message', '')
                    
                    # Calculate total pages from rows
                    rows_match = re.search(r'rows=(\d+)', message, re.IGNORECASE)
                    total_pages = (int(rows_match.group(1)) + self.config.PAGE_SIZE - 1) // self.config.PAGE_SIZE if rows_match else 1
                    
                    self.report_status_store[report_id].update({
                        'status': state,
                        'message': message,
                        'total_pages': total_pages
                    })
                    
                    logger.debug(f"Report '{report_key.upper()}' status: {state}")
                    
                    if state == "FinishedSuccess":
                        data = self._fetch_report_data(api_report_id, report_key, total_pages)
                        self.report_data_store[report_id] = data
                        logger.info(f"Report '{report_key.upper()}' completed successfully")
                        break
                    elif state == "FinishedError":
                        logger.error(f"Report '{report_key.upper()}' failed: {message}")
                        break
                    
                    time.sleep(5)
                except Exception as e:
                    self.report_status_store[report_id]['status'] = 'FinishedError'
                    self.report_status_store[report_id]['message'] = str(e)
                    logger.error(f"Error polling report '{report_key.upper()}': {e}")
                    break
        
        thread = threading.Thread(target=poll)
        thread.daemon = True
        thread.start()

    def _fetch_report_data(self, api_report_id: str, report_key: str, total_pages: int) -> List[Dict[str, Any]]:
        """Fetch report data from all pages."""
        access_token = self.get_access_token()
        output_endpoint = f"/api/abareport/v1/jobs/{api_report_id}/output"
        all_data = []
        
        try:
            for page in range(1, total_pages + 1):
                logger.debug(f"Fetching page {page} for report '{report_key.upper()}'")
                response = requests.get(
                    f"{self.config.BASE_URL}{output_endpoint}/{page}",
                    headers={
                        'Authorization': f'Bearer {access_token}',
                        'Content-Type': 'application/json'
                    }
                )
                
                if response.status_code == 404:
                    logger.warning(f"Page {page} not found for report '{report_key.upper()}'")
                    break
                
                response.raise_for_status()
                data = response.json()
                
                if isinstance(data, list) and data:
                    all_data.extend(data)
                    logger.debug(f"Added {len(data)} records from page {page}")
                else:
                    logger.warning(f"No data on page {page} for report '{report_key.upper()}'")
                    break
            
            logger.info(f"Fetched total {len(all_data)} records for report '{report_key.upper()}'")
            return all_data
        except Exception as e:
            logger.error(f"Error fetching report data: {e}")
            raise

    def get_report_status(self, report_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific report."""
        return self.report_status_store.get(report_id)

    def get_report_data(self, report_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get data of a completed report."""
        return self.report_data_store.get(report_id)

    def get_all_reports(self) -> List[Dict[str, Any]]:
        """Get status of all reports."""
        return [
            {
                'report_id': report_id,
                'report_key': status['report_key'],
                'status': status['status'],
                'message': status['message']
            }
            for report_id, status in self.report_status_store.items()
        ]
