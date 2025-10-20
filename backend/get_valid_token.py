import requests
import json

def get_valid_token():
    try:
        # 使用默认的管理员凭据
        login_data = {
            'username': 'admin',
            'password': 'admin123'
        }
        
        response = requests.post(
            'http://localhost:8000/api/auth/login',
            json=login_data,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            data = response.json()
            token = data.get('access_token')
            print(f"✓ Login successful")
            print(f"✓ Token: {token[:50]}...")
            return token
        else:
            print(f"✗ Login failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"✗ Error getting token: {e}")
        return None

if __name__ == "__main__":
    token = get_valid_token()
    if token:
        print(f"\nValid token obtained: {token}")
    else:
        print("\nFailed to get valid token")