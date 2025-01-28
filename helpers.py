import logging
import re
import time
import uuid
import threading
import requests
import base64
from typing import Dict, List, Any, Optional

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class ReportManager:
    def __init__(self, config):
        self.config = config
        self.report_status_store: Dict[str, Dict[str, Any]] = {}
        self.report_data_store: Dict[str, List[Dict[str, Any]]] = {}
        self.report_keys = config['COMPANIES']['uniska']['report_keys']

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

                response = requests.post(
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
            response = requests.post(
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

                    response = requests.get(
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
        access_token = self.get_access_token()
        output_endpoint = f"/api/abareport/v1/jobs/{api_report_id}/output"
        all_data = []

        try:
            for page in range(1, total_pages + 1):
                logger.debug(f"Fetching page {page} for report '{report_key.upper()}'")
                response = requests.get(
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

        # Define the exact columns we want from each table
        NPO_COLUMNS = [
            'ProjNr', 'ProjName', 'KdINR', 'RootProj', 'Name2', 'Name3', 'ISOCode',
            'Status', 'Status1', 'Status2', 'Status3', 'Status4', 'KDatum', 'KSumme',
            'ADatum', 'ASumme', 'NDatum', 'NSumme', 'Person1'
        ]

        ADR_COLUMNS = [
            'INR', 'KURZNA', 'LAND', 'PLZ', 'NAME', 'VORNAME', 'ORT', 'SUBJEKTTYP',
            'IS_AKP_ONLY', 'EMAIL', 'ZEILE1', 'ZEILE2', 'STAAT', 'STREET', 'ANR_NR',
            'ANREDENAME', 'TEL', 'TEL2', 'TELEX', 'TELEFAX', 'SPRACHE', 'ASI_INR',
            'AKP_NR', 'WWW', 'HOUSE_NUMBER', 'AddressAddition', 'StreetAddition',
            'PostOfficeBoxText', 'PostOfficeBoxNumber', 'ANR_GROUP'
        ]

        AKP_COLUMNS = [
            'ADR_INR', 'NR', 'NAME', 'VORNAME', 'FUNKTION', 'SUBJEKT_NR', 'ANR_NR',
            'ANREDENAME', 'TEL', 'MAIL', 'WWW', 'TEL2', 'TEL3', 'TEL4', 'ABTEILUNG',
            'ANR_GROUP'
        ]

        ANR_COLUMNS = [
            'NR', 'Group', 'ANREDE', 'ANREDETEXT'
        ]

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
            key = str(npo.get('KdINR', '')) if npo.get('Person1') == '0' else str(npo.get('Person1', ''))
            if key:
                npo_dict[key] = npo

        adr_dict = {str(adr.get('INR', '')): adr for adr in adr_data if adr.get('INR')}

        # Create AKP lookup dictionary
        akp_dict = {}
        anr_dict = {}

        # Get ANR data from report store if available
        for report_id, status in self.report_status_store.items():
            if status['report_key'] == 'anr' and status['status'] == 'FinishedSuccess':
                anr_data = self.report_data_store.get(report_id, [])
                anr_dict = {str(anr.get('NR')): anr.get('ANR_NR') for anr in anr_data if anr.get('NR')}
                break

        if akp_data:
            for akp in akp_data:
                adr_inr = str(akp.get('ADR_INR', ''))
                akp['ANR_NR'] = anr_dict.get(str(akp.get('NR', '')), '')
                if adr_inr:
                    if adr_inr not in akp_dict:
                        akp_dict[adr_inr] = []
                    akp_dict[adr_inr].append(akp)

        # Combine data based on matching keys
        combined_data = []
        processed_records = set()

        # First pass: Process NPO records
        for inr, npo in npo_dict.items():
            adr = adr_dict.get(inr)
            akp_entries = akp_dict.get(inr, [])

            if adr:
                # Create combined record with all NPO fields
                combined_record = {k: npo.get(k, '') for k in npo.keys()}

                # Add all ADR fields
                adr_fields = {f'ADR_{k}': v for k, v in adr.items()}
                combined_record.update(adr_fields)

                # Add status field if not present
                combined_record['Status'] = 'new'

                # Add commonly used fields at their usual locations
                common_fields = {
                    'NAME': adr.get('NAME', ''),
                    'VORNAME': '',  # Will be populated from AKP if available
                    'EMAIL': '',    # Will be populated from AKP if available
                    'TEL': adr.get('TEL', ''),
                    'LAND': adr.get('LAND', ''),
                    'PLZ': adr.get('PLZ', ''),
                    'ORT': adr.get('ORT', ''),
                    'STREET': adr.get('STREET', ''),
                    'HOUSE_NUMBER': adr.get('HOUSE_NUMBER', '')
                }
                combined_record.update(common_fields)

                # Add AKP data if available
                if akp_entries:
                    akp_data = akp_entries[0]  # Take first entry
                    for k, v in akp_data.items():
                        combined_record[f'AKP_{k}'] = v

                combined_data.append(combined_record)
                processed_records.add(inr)

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