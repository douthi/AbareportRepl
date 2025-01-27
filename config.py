
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # Flask configuration
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'dev_secret_key')
    DEBUG = True

    # Abacus ERP configuration
    CLIENT_ID = os.getenv('CLIENT_ID')
    CLIENT_SECRET = os.getenv('CLIENT_SECRET')
    TOKEN_URL = 'https://abacus.indutrade.ch/oauth/oauth2/v1/token'
    BASE_URL = os.getenv('BASE_URL', 'https://abacus.indutrade.ch')
    PAGE_SIZE = int(os.getenv('PAGE_SIZE', '1000'))

    # Company configurations
    COMPANIES = {
        'uniska': {
            'name': 'Uniska AG',
            'pipedrive_api_key': os.getenv('UNISKA_PIPEDRIVE_API_KEY'),
            'mandants': {
                "19": "Uniska Interiors",
                "20": "Uniska AG"
            },
            'report_keys': {
                "adr": "uniska_pipedrive_adr",
                "akp": "uniska_pipedrive_akp",
                "anr": "uniska_pipedrive_anr",
                "npo": "uniska_pipedrive_npo"
            }
        },
        'novisol': {
            'name': 'Novisol',
            'pipedrive_api_key': os.getenv('NOVISOL_PIPEDRIVE_API_KEY'),
            'mandants': {
                "2": "Novisol AG, Rheinfelden",
                "7": "Novisol GmbH, Weil am Rhein"
            },
            'report_keys': {
                "adr": "novisol_pipedrive_adr",
                "akp": "novisol_pipedrive_akp",
                "anr": "novisol_pipedrive_anr",
                "npo": "novisol_pipedrive_npo"
            }
        }
    }
