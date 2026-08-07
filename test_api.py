import requests
import json

base_url = "http://127.0.0.1:8000"

res = requests.post(f"{base_url}/auth/signup", json={"username": "testuser2", "email": "test2@test.com", "password": "password123"})
if res.status_code != 201:
    res = requests.post(f"{base_url}/auth/signin", json={"username": "testuser2", "password": "password123"})

token = res.json().get("access_token")
if not token:
    print("NO TOKEN:", res.text)
else:
    headers = {"Authorization": f"Bearer {token}"}
    res = requests.post(f"{base_url}/tickets", json={"title": "Test Ticket", "description": "Desc", "category": "Hardware", "priority": "Low"}, headers=headers)
    print("CREATE:", res.text)
    res = requests.get(f"{base_url}/tickets", headers=headers)
    print("GET TICKETS:", json.dumps(res.json(), indent=2))
