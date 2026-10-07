import requests
from django.conf import settings

HEADERS = {
    "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
    "Content-Type": "application/json",
}


def initialize_transaction(email, amount_ghs, reference, callback_url, metadata=None):
    payload = {
        "email": email,
        "amount": int(round(amount_ghs * 100)),
        "currency": "GHS",
        "reference": reference,
        "callback_url": callback_url,
        "channels": ["mobile_money", "card"],
        "metadata": metadata or {},
    }
    resp = requests.post(
        f"{settings.PAYSTACK_BASE_URL}/transaction/initialize",
        json=payload, headers=HEADERS, timeout=15,
    )
    resp.raise_for_status()
    return resp.json()["data"]


def verify_transaction(reference):
    resp = requests.get(
        f"{settings.PAYSTACK_BASE_URL}/transaction/verify/{reference}",
        headers=HEADERS, timeout=15,
    )
    resp.raise_for_status()
    return resp.json()["data"]


def create_transfer_recipient(name, momo_number, momo_network):
    network_codes = {"mtn": "MTN", "vodafone": "VOD", "airteltigo": "ATL"}
    payload = {
        "type": "mobile_money",
        "name": name,
        "account_number": momo_number,
        "bank_code": network_codes.get(momo_network, "MTN"),
        "currency": "GHS",
    }
    resp = requests.post(
        f"{settings.PAYSTACK_BASE_URL}/transferrecipient",
        json=payload, headers=HEADERS, timeout=15,
    )
    resp.raise_for_status()
    return resp.json()["data"]


def initiate_transfer(recipient_code, amount_ghs, reason):
    payload = {
        "source": "balance",
        "amount": int(round(amount_ghs * 100)),
        "recipient": recipient_code,
        "reason": reason,
    }
    resp = requests.post(
        f"{settings.PAYSTACK_BASE_URL}/transfer",
        json=payload, headers=HEADERS, timeout=15,
    )
    resp.raise_for_status()
    return resp.json()["data"]
