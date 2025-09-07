import requests
import json

url = 'http://localhost:8000/payments/create-order'
headers = {'Content-Type': 'application/json'}
data = {
    'student_id': 1,
    'amount': 5000,
    'month': 9,
    'year': 2025
}

try:
    response = requests.post(url, headers=headers, data=json.dumps(data))
    print(f'Status Code: {response.status_code}')
    if response.status_code == 200:
        result = response.json()
        print('Success! Response contains:')
        print(f'- order_id: {result.get("order_id")}')
        print(f'- upi_url: {result.get("upi_url")}')
        print(f'- payment_id: {result.get("payment_id")}')
        print(f'- qr_base64 length: {len(result.get("qr_base64", ""))} characters')
    else:
        print(f'Error: {response.text}')
except Exception as e:
    print(f'Error: {e}')
    print('Make sure the FastAPI server is running on port 8000')
