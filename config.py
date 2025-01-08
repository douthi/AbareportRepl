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
    PAGE_SIZE = int(os.getenv('PAGE_SIZE', '1000')) # Changed page size to 1000

    # Report keys mapping
    REPORT_KEYS = {
        "adr": "uniska_pipedrive_adr",
        "akp": "uniska_pipedrive_akp",
        "anr": "uniska_pipedrive_anr",
        "npo": "uniska_pipedrive_npo",
    }

    # Supported mandants
    SUPPORTED_MANDANTS = {
        "19": "Uniska Interiors",
        "20": "Uniska AG",
    }