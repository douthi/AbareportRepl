import logging
import re
import time
import uuid
import threading
import requests
import base64
from typing import Dict, List, Any, Optional
from replit import db

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class ReportManager:
    def __init__(self, config):
        self.config = config
        self.report_status_store: Dict[str, Dict[str, Any]] = {}
        self.report_data_store: Dict[str, List[Dict[str, Any]]] = {}
        self.report_keys = config['COMPANIES']['uniska']['report_keys']
        self.session = requests.Session()
        self.cache = {}
        self.cache_timeout = 300  # 5 minutes

    def get_access_token(self) -> str:
        """Get access token from Abacus ERP."""
        max_retries = 3
        timeout = 30

        for attempt in range(max_retries):
            try:
                logger.debug(f"Using CLIENT_ID: {self.config['CLIENT_ID']}")
                logger.debug(f"Using CLIENT_SECRET length: {len(self.config['CLIENT_SECRET']) if self.config['CLIENT_SECRET'] else 0}")
                # Encode credentials for basic auth
                credentials = f"{self.config['CLIENT_ID']}:{self.config['CLIENT_SECRET']}"
                auth_header = f"Basic {base64.b64encode(credentials.encode()).decode()}"

                response = self.session.post(
                    self.config['TOKEN_URL'],
                    data='grant_type=client_credentials',
                    headers={
                        'Accept-Charset': 'UTF-8',
                        'Content-Type': 'application/x-www-form-urlencoded',
                        'Authorization': auth_header,
                        'Accept': '*/*'
                    },
                    timeout=timeout
                )
                response.raise_for_status()
                access_token = response.json().get('access_token')
                logger.debug("Access token obtained successfully")
                return access_token
            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:
                    logger.error(f"Error obtaining access token after {max_retries} attempts: {e}")
                    raise
                logger.warning(f"Attempt {attempt + 1} failed, retrying: {e}")
                time.sleep(2 ** attempt)  # Exponential backoff

    def start_report(self, mandant: str, report_key: str, year: str) -> str:
        """Start a report and return the report ID."""
        access_token = self.get_access_token()
        report_id = str(uuid.uuid4())
        logger.info(f"Starting report {report_key} for mandant {mandant}")

        self.report_status_store[report_id] = {
            'mandant': mandant,
            'report_key': report_key,
            'api_report_id': None,
            'status': 'Running',
            'message': 'Report started.',
            'total_pages': 1
        }

        report_path = self.report_keys[report_key]
        # Format mandant ID with leading zeros if needed
        formatted_mandant = f"{int(mandant):02d}"
        endpoint = f"/api/abareport/v1/report/{formatted_mandant}/{report_path}"

        # Build request body
        body = {
            "outputType": "json",
            "paging": self.config['PAGE_SIZE']
        }

        # Add date parameters for dko report
        if report_key == "dko" and year != "none":
            body["parameters"] = {
                "AUF_DATUM_VON": f"{year}-01-01",
                "AUF_DATUM_BIS": f"{year}-12-31"
            }

        try:
            response = self.session.post(
                f"{self.config['BASE_URL']}{endpoint}",
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

                    response = self.session.get(
                        f"{self.config['BASE_URL']}{status_endpoint}",
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
                    total_pages = (int(rows_match.group(1)) + self.config['PAGE_SIZE'] - 1) // self.config['PAGE_SIZE'] if rows_match else 1

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
        cache_key = f"{api_report_id}-{report_key}"
        if cache_key in self.cache and time.time() - self.cache[cache_key]['timestamp'] < self.cache_timeout:
            logger.debug(f"Using cached data for report '{report_key.upper()}'")
            return self.cache[cache_key]['data']

        access_token = self.get_access_token()
        output_endpoint = f"/api/abareport/v1/jobs/{api_report_id}/output"
        all_data = []

        try:
            for page in range(1, total_pages + 1):
                logger.debug(f"Fetching page {page} for report '{report_key.upper()}'")
                response = self.session.get(
                    f"{self.config['BASE_URL']}{output_endpoint}/{page}",
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
            self.cache[cache_key] = {'data': all_data, 'timestamp': time.time()}
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

    def get_combined_data(self) -> List[Dict[str, Any]]:
        """Get combined and matched data from NPO, ADR, and AKP reports."""
        combined_data = []

        # Get the latest report data for each type
        npo_data = None
        adr_data = None
        akp_data = None

        for report_id, status in self.report_status_store.items():
            if status['status'] == 'FinishedSuccess':
                if status['report_key'] == 'npo':
                    npo_data = self.report_data_store.get(report_id)
                elif status['report_key'] == 'adr':
                    adr_data = self.report_data_store.get(report_id)
                elif status['report_key'] == 'akp':
                    akp_data = self.report_data_store.get(report_id)

        if not all([npo_data, adr_data]):
            return []  # Return empty if required data is missing

        # Create lookup dictionaries
        npo_dict = {}
        for npo in npo_data:
            if not npo.get('ProjNr'):  # Skip if no project number
                continue
            key = str(npo.get('KdINR', '')) if npo.get('Person1') == '0' else str(npo.get('Person1', ''))
            if key:
                npo_dict[key] = npo

        adr_dict = {str(adr.get('INR', '')): adr for adr in adr_data if adr.get('INR')}

        # Create lookup dictionaries for AKP
        akp_dict = {}
        if akp_data:
            for akp in akp_data:
                adr_inr = str(akp.get('ADR_INR', ''))
                if adr_inr:
                    if adr_inr not in akp_dict:
                        akp_dict[adr_inr] = []
                    akp_dict[adr_inr].append(akp)

        # Process NPO records
        for inr, npo in npo_dict.items():
            adr = adr_dict.get(inr)
            if not adr:
                continue

            # Create base record with NPO data
            base_record = {f'NPO_{k}': v for k, v in npo.items()}

            # Handle ADR phone fallback
            adr_phone = adr.get('TEL') or adr.get('TEL2') or ''
            adr_with_phone = {**adr, 'TEL': adr_phone}

            # Add ADR fields with prefix
            adr_fields = {f'ADR_{k}': v for k, v in adr_with_phone.items()}
            base_record.update(adr_fields)

            # Add status field
            base_record['Status'] = 'new'

            # Get all AKP entries for this ADR
            akp_entries = akp_dict.get(inr, [])
            
            if not akp_entries:  # If no AKP entries, add base record
                combined_data.append(base_record)
                continue

            # Create a record for each AKP entry
            for akp_record in akp_entries:
                current_record = base_record.copy()

                # Handle AKP phone fallback
                akp_phone = akp_record.get('TEL') or akp_record.get('TEL2') or akp_record.get('TEL3') or ''
                akp_with_phone = {**akp_record, 'TEL': akp_phone}

                # Add AKP fields with prefix
                akp_fields = {f'AKP_{k}': v for k, v in akp_with_phone.items()}
                current_record.update(akp_fields)

                # Add ANR fields based on AKP_ANR_NR
                anr_nr = akp_record.get('ANR_NR')
                if anr_nr:
                    try:
                        import csv
                        with open('attached_assets/ANR.csv', 'r') as f:
                            anr_reader = csv.DictReader(f)
                            for row in anr_reader:
                                if row['NR'] == str(anr_nr):
                                    current_record['ANR_ANREDE'] = row['ANREDE']
                                    current_record['ANR_ANREDETEXT'] = row['ANREDETEXT']
                                    break
                    except Exception as e:
                        logger.error(f"Error reading ANR data: {e}")

                combined_data.append(current_record)

        return combined_data

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