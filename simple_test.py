import requests
import json

print("Testing device API...")

try:
    # Test login first
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    print("1. Testing login...")
    login_response = requests.post("http://localhost:8001/api/auth/login", json=login_data)
    print(f"Login status: {login_response.status_code}")
    
    if login_response.status_code == 200:
        token = login_response.json().get("access_token")
        print(f"Token received: {token[:20]}...")
        
        # Test devices API
        headers = {"Authorization": f"Bearer {token}"}
        print("\n2. Testing devices API...")
        devices_response = requests.get("http://localhost:8001/api/devices", headers=headers)
        print(f"Devices API status: {devices_response.status_code}")
        print(f"Response: {devices_response.text}")
        
    else:
        print(f"Login failed: {login_response.text}")
        
except Exception as e:
    print(f"Error: {e}")

print("Test completed.")