
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
            },
            'field_mappings': [
                {"source": "NPO_ProjNr", "target": "5d300cf82930e07f6107c7255fcd0dd550af7774", "entity": "deal"},
                {"source": "NPO_ProjName", "target": "title", "entity": "deal"},
                {"source": "NPO_KSumme", "target": "value", "entity": "deal"},
                {"source": "NPO_KDatum", "target": "add_time", "entity": "deal"},
                {"source": "NPO_ADatum", "target": "close_time", "entity": "deal"},
                {"source": "NPO_Status4Date", "target": "lost_time", "entity": "deal"},
                {"source": "ADR_NAME", "target": "name", "entity": "organization"},
                {"source": "ADR_TEL", "target": "a82d57b1a943fc63f5c1130cd7e2af78f8a3b6b0", "entity": "organization"},
                {"source": "ADR_LAND", "target": "address_country", "entity": "organization"},
                {"source": "ADR_PLZ", "target": "address_postal_code", "entity": "organization"},
                {"source": "ADR_ORT", "target": "address_locality", "entity": "organization"},
                {"source": "ADR_STREET", "target": "address_route", "entity": "organization"},
                {"source": "ADR_HOUSE_NUMBER", "target": "address_street_number", "entity": "organization"},
                {"source": "AKP_NAME", "target": "last_name", "entity": "person"},
                {"source": "AKP_VORNAME", "target": "first_name", "entity": "person"},
                {"source": "AKP_FUNKTION", "target": "job_title", "entity": "person"},
                {"source": "AKP_TEL", "target": "phone", "entity": "person"},
                {"source": "AKP_MAIL", "target": "email", "entity": "person"},
                {"source": "ANR_ANREDE", "target": "031ae26196cff3bf754a3fa9ff701f13c73113bf", "entity": "person"},
                {"source": "ANR_ANREDETEXT", "target": "7bcef1831b6beeb06bcdd031e8ce321626dc644a", "entity": "person"}
            ],
            'field_keys': {
                'salutation_text': '7bcef1831b6beeb06bcdd031e8ce321626dc644a'
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
            },
            'field_keys': {
                'project_number': 'f5f8535453d1498befe27d2dfe90a680f10fd616',
                'salutation': 'a1e33efdca526d9b12b21bc5594e11f8e017824b',
                'salutation_text': 'd70aa79b28126a53cf4260fc23beeba271b7255f',
                'company_phone': '300867ce076894528208878f4f7ec1d684fabbc9'
            }
        }
    }
