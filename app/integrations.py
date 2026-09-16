"""Authorization-gated adapters. No external write is possible without explicit enablement."""
from __future__ import annotations
import os
from dataclasses import dataclass

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

def allow_external_write(enabled: bool, approved: bool) -> bool:
    return bool(enabled and approved)
