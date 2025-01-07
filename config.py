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
    TOKEN_URL = os.getenv('TOKEN_URL')
    BASE_URL = os.getenv('BASE_URL', 'https://abacus.indutrade.ch')
    PAGE_SIZE = int(os.getenv('PAGE_SIZE', '200'))

    # Report keys mapping
    REPORT_KEYS = {
        "adr": "uniska_pipedrive_adr",
        "akp": "uniska_pipedrive_akp",
        "anr": "uniska_pipedrive_anr",
        "zla": "uniska_pipedrive_zla",
        "npo": "uniska_pipedrive_npo",
        "dko": "uniska_pipedrive_dko",
    }

    # Supported mandants
    SUPPORTED_MANDANTS = {
        "19": "Uniska Interiors",
        "20": "Uniska AG",
    }
