import requests

url = "http://127.0.0.1:8000/query"

payload = {
    "type": "qa",
    "question": "What is dirty air in Formula 1?",
    "driver_id": "44",
    "lap": 10
}

response = requests.post(url, json=payload)

print("Status:", response.status_code)
print("Response JSON:")
print(response.json())
