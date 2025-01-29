
import requests
import os
import base64
import logging
from config import Config

# Configure logging
logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_endpoint():
    try:
        # Get access token
        credentials = f"{Config.CLIENT_ID}:{Config.CLIENT_SECRET}"
        auth_header = f"Basic {base64.b64encode(credentials.encode()).decode()}"
        
        logger.info("Attempting to get access token...")
        token_response = requests.post(
            Config.TOKEN_URL,
            data='grant_type=client_credentials',
            headers={
                'Accept-Charset': 'UTF-8',
                'Content-Type': 'application/x-www-form-urlencoded',
                'Authorization': auth_header,
                'Accept': '*/*'
            },
            timeout=30
        )
        
        if token_response.status_code == 200:
            access_token = token_response.json().get('access_token')
            logger.info("Token obtained successfully")
            
            # Test report endpoint
            mandant = "19"  # Test mandant
            report_path = "uniska_pipedrive_adr"  # Test report
            endpoint = f"/api/abareport/v1/report/{mandant}/{report_path}"
            
            logger.info(f"Testing endpoint: {endpoint}")
            response = requests.get(
                f"{Config.BASE_URL}{endpoint}",
                headers={'Authorization': f'Bearer {access_token}'},
                timeout=30
            )
            
            logger.info(f"Status Code: {response.status_code}")
            logger.debug(f"Response: {response.text}")
            
        else:
            logger.error(f"Token request failed: {token_response.status_code}")
            logger.error(f"Response: {token_response.text}")
            
    except requests.exceptions.Timeout:
        logger.error("Request timed out")
    except requests.exceptions.ConnectionError:
        logger.error("Connection error occurred")
    except Exception as e:
        logger.error(f"Error: {str(e)}")

if __name__ == "__main__":
    test_endpoint()
