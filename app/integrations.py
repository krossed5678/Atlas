"""Authorization-gated adapters. No external write is possible without explicit enablement."""
from __future__ import annotations
import os
from dataclasses import dataclass

DEFAULT_SHOPIFY_STORE = "x6qufc-nh.myshopify.com"
KOFI_ROSSI_STRIPE_CONTEXT = "acct_1SPAFpI0vp8qwDso"

@dataclass
class Readiness:
    service:str; ready:bool; reason:str

def readiness() -> list[Readiness]:
    return [
      Readiness('OpenAI',bool(os.getenv('ASTRA_OPENAI_API_KEY')),'API key required'),
      Readiness('Mailbox',False,'OAuth authorization required'),
      Readiness('TikTok Shop',bool(os.getenv('ASTRA_TIKTOK_SHOP_CLIENT_KEY')),'Business app authorization required'),
      Readiness('Stripe Connect',bool(os.getenv('ASTRA_STRIPE_SECRET_KEY')),'Account, KYC, legal/tax authorization required'),
      Readiness('Robinhood',bool(os.getenv('ASTRA_ROBINHOOD_CRYPTO_API_KEY')),'Official Agentic/Crypto authorization required'),
    ]


def commerce_configuration() -> dict[str, str | bool]:
    """Non-secret account selection; credentials are read only from the local environment."""
    return {
        "shopify_store": os.getenv("ASTRA_SHOPIFY_STORE_DOMAIN", DEFAULT_SHOPIFY_STORE),
        "stripe_context": os.getenv("ASTRA_STRIPE_CONTEXT", KOFI_ROSSI_STRIPE_CONTEXT),
        "stripe_livemode": os.getenv("ASTRA_STRIPE_LIVEMODE", "false").lower() == "true",
        "stripe_connect_flow": "marketplace_recipient_v2_separate_charges_and_transfers",
        "creator_payouts": "human_approval_required",
    }

def allow_external_write(enabled: bool, approved: bool) -> bool:
    return bool(enabled and approved)
