"""Click & Payme checkout URL builders for Uzbekistan SaaS subscriptions."""

from __future__ import annotations

import base64
import os
import secrets
from urllib.parse import urlencode


def build_checkout(provider: str, amount_uzs: int, plan_id: str, business_name: str) -> dict[str, str]:
    """Generate a sandbox/live-ready invoice code and checkout URL for Click or Payme."""
    invoice_code = f"INV-{secrets.token_hex(3).upper()}"
    provider_clean = provider.lower().strip()

    if provider_clean == "click":
        merchant_id = os.environ.get("CLICK_MERCHANT_ID", "DEMO_MERCHANT")
        service_id = os.environ.get("CLICK_SERVICE_ID", "DEMO_SERVICE")
        base_url = os.environ.get("APP_BASE_URL", "http://127.0.0.1:8080").rstrip("/")
        params = urlencode(
            {
                "service_id": service_id,
                "merchant_id": merchant_id,
                "amount": amount_uzs,
                "transaction_param": invoice_code,
                "return_url": f"{base_url}/?paid=click",
            }
        )
        checkout_url = f"https://my.click.uz/services/pay?{params}"
        is_demo = merchant_id == "DEMO_MERCHANT"
    elif provider_clean == "payme":
        merchant_id = os.environ.get("PAYME_MERCHANT_ID", "DEMO_PAYME_ID")
        amount_tiyin = amount_uzs * 100
        raw = f"m={merchant_id};ac.order_id={invoice_code};ac.plan={plan_id};ac.biz={business_name};a={amount_tiyin}"
        encoded = base64.b64encode(raw.encode("utf-8")).decode("ascii")
        checkout_url = f"https://checkout.paycom.uz/{encoded}"
        is_demo = merchant_id == "DEMO_PAYME_ID"
    else:
        raise ValueError("Faqat 'click' yoki 'payme' qo'llab-quvvatlanadi")

    return {
        "invoice_code": invoice_code,
        "provider": provider_clean,
        "checkout_url": checkout_url,
        "mode": "demo" if is_demo else "live",
    }
