# Activation runbook

## Robinhood Agentic

1. Use only the official Robinhood Agentic account/MCP connection flow.
2. Enable Developer Mode and connect the account in Robinhood's own approval UI.
3. Store no Robinhood username or password in this project.
4. Keep `live_trading_allowed=false`; the platform produces a reviewable, idempotent order handoff only.

Browser status: BrowserAct 1.4.2 is installed. The official `robinhood-trading` Streamable HTTP MCP is registered globally in Codex and OAuth was approved on 2026-09-16. A privacy-minimized read-only `get_accounts` verification succeeded (four linked accounts; account numbers, balances, positions, and orders were not retrieved or logged). ASTRA continues to default to PAPER, and its live gate remains locked.

## Shopify and TikTok Shop

Supply an Admin API access token and TikTok Shop app credentials via environment variables. The application must first pass read-only health and webhook signature tests. Publishing stays disabled unless a calendar item has explicit approval.

## Stripe Connect and email

Creator contracts, KYC/tax readiness, connected-account capability status, and payout approval must all be true before a payout may be submitted. Mail sending requires OAuth and per-message approval.
