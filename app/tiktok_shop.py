"""Configuration gate for TikTok Shop merchant integration.

Network calls are intentionally absent until the seller completes the official
merchant OAuth flow and supplies credentials through local encrypted settings.
"""
from __future__ import annotations

import os

PUBLIC_SITE = "https://krossed5678.github.io/"


def readiness() -> dict:
    missing=[]
    for key in ("ASTRA_TIKTOK_SHOP_CLIENT_KEY", "ASTRA_TIKTOK_SHOP_CLIENT_SECRET", "ASTRA_TIKTOK_MERCHANT_ID", "ASTRA_TIKTOK_REDIRECT_URI"):
        if not os.getenv(key): missing.append(key)
    redirect=os.getenv("ASTRA_TIKTOK_REDIRECT_URI","")
    if redirect and not redirect.startswith("https://"): missing.append("ASTRA_TIKTOK_REDIRECT_URI must use HTTPS")
    return {"ready":not missing,"missing":missing,"public_site":PUBLIC_SITE,"mode":"DRAFT_ONLY","writes_enabled":False,"next_step":"Complete official merchant authorization; do not place credentials in source files."}
