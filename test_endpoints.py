
import requests
import os
from config import Config

def test_endpoint():
    try:
        # Get access token
        credentials = f"{Config.CLIENT_ID}:{Config.CLIENT_SECRET}"
        auth_header = f"Basic {base64.b64encode(credentials.encode()).decode()}"
        
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
            print("Token obtained successfully")
            
            # Test report endpoint
            mandant = "19"  # Test mandant
            report_path = "uniska_pipedrive_adr"  # Test report
            endpoint = f"/api/abareport/v1/report/{mandant}/{report_path}"
            
            response = requests.get(
                f"{Config.BASE_URL}{endpoint}",
                headers={'Authorization': f'Bearer {access_token}'},
                timeout=30
            )
            
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            
        else:
            print(f"Token request failed: {token_response.status_code}")
            print(token_response.text)
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_endpoint()
