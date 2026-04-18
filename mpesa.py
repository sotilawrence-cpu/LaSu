import requests
import base64
from datetime import datetime

# -------------------------
# CONFIG (replace with yours)
# -------------------------
CONSUMER_KEY = "YOUR_CONSUMER_KEY"
CONSUMER_SECRET = "YOUR_CONSUMER_SECRET"
BUSINESS_SHORT_CODE = "174379"
PASSKEY = "YOUR_PASSKEY"
CALLBACK_URL = "https://abcd1234.ngrok.io/mpesa/callback"

# -------------------------
# GET ACCESS TOKEN
# -------------------------
def get_access_token():
    url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"

    response = requests.get(
        url,
        auth=(CONSUMER_KEY, CONSUMER_SECRET)
    )

    return response.json()['access_token']

# -------------------------
# STK PUSH
# -------------------------
def stk_push(phone, amount):
    access_token = get_access_token()

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    password = base64.b64encode(
        (BUSINESS_SHORT_CODE + PASSKEY + timestamp).encode()
    ).decode('utf-8')

    url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"

    headers = {
        "Authorization": "Bearer " + access_token,
        "Content-Type": "application/json"
    }

    payload = {
        "BusinessShortCode": BUSINESS_SHORT_CODE,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": amount,
        "PartyA": phone,
        "PartyB": BUSINESS_SHORT_CODE,
        "PhoneNumber": phone,
        "CallBackURL": CALLBACK_URL,
        "AccountReference": "LoanPayment",
        "TransactionDesc": "Loan repayment"
    }

    response = requests.post(url, json=payload, headers=headers)

    return response.json()