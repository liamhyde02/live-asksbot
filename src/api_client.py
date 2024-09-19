import requests
from config import API_BASE_URL, API_KEY

def call_api(endpoint, method="GET", params=None, json=None):
    url = f"{API_BASE_URL}{endpoint}"
    headers = {"access_token": API_KEY}
    
    try:
        if method == "GET":
            response = requests.get(url, params=params, headers=headers)
        elif method == "POST":
            response = requests.post(url, params=params, json=json, headers=headers)
        
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"API call failed: {str(e)}")
        return None

def get_customer_org_id(team_id):
    response = call_api("/customerorganization/slack", params={"slack_id": str(team_id)})
    return response.get("customer_organization_id") if response else None

def get_user_id(slack_id):
    response = call_api("/user/slack", params={"slack_id": str(slack_id)})
    return response.get("user_id") if response else None