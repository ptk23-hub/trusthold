import os
import requests
from dotenv import load_dotenv

load_dotenv()
BASE_URL = "https://api-m.sandbox.paypal.com"


def get_token():
    response = requests.post(
        f"{BASE_URL}/v1/oauth2/token",
        auth=(os.getenv("PAYPAL_CLIENT_ID"), os.getenv("PAYPAL_CLIENT_SECRET")),
        data={"grant_type": "client_credentials"},
    )
    response.raise_for_status()
    return response.json()["access_token"]


def _headers():
    return {"Authorization": f"Bearer {get_token()}", "Content-Type": "application/json"}


def create_order(amount, description, return_url):
    """Client's offer. AUTHORIZE means: hold the money, don't take it yet."""
    body = {
        "intent": "AUTHORIZE",
        "purchase_units": [
            {
                "description": description,
                "amount": {"currency_code": "USD", "value": f"{float(amount):.2f}"},
            }
        ],
        "payment_source": {
            "paypal": {
                "experience_context": {
                    "return_url": return_url,
                    "cancel_url": return_url + "/?cancelled=1",
                }
            }
        },
    }
    r = requests.post(f"{BASE_URL}/v2/checkout/orders", headers=_headers(), json=body)
    r.raise_for_status()
    data = r.json()
    link = next(l["href"] for l in data["links"] if l["rel"] in ("payer-action", "approve"))
    return data["id"], link


def authorize_order(order_id):
    """PayPal holds the money. Returns the authorization ID."""
    r = requests.post(f"{BASE_URL}/v2/checkout/orders/{order_id}/authorize", headers=_headers())
    r.raise_for_status()
    return r.json()["purchase_units"][0]["payments"]["authorizations"][0]["id"]


def capture_payment(auth_id):
    """Release the held money to the freelancer."""
    r = requests.post(
        f"{BASE_URL}/v2/payments/authorizations/{auth_id}/capture",
        headers=_headers(),
        json={"final_capture": True},
    )
    r.raise_for_status()
    return r.json()["status"]


def void_payment(auth_id):
    """Cancel the hold. The client keeps their money."""
    r = requests.post(f"{BASE_URL}/v2/payments/authorizations/{auth_id}/void", headers=_headers())
    r.raise_for_status()