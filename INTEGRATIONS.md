# Activation runbook

## Robinhood Agentic

1. Use only the official Robinhood Agentic account/MCP connection flow.
2. Enable Developer Mode and connect the account in Robinhood's own approval UI.
3. Store no Robinhood username or password in this project.
4. Keep `live_trading_allowed=false`; the platform produces a reviewable, idempotent order handoff only.

Browser status: BrowserAct 1.4.2 is installed and Robinhood’s official Agentic guidance was opened. Creating the MCP connection is intentionally waiting for the user’s action-time confirmation because it creates persistent access to brokerage account data and potential Agentic-account trading access.

## Shopify and TikTok Shop

Supply an Admin API access token and TikTok Shop app credentials via environment variables. The application must first pass read-only health and webhook signature tests. Publishing stays disabled unless a calendar item has explicit approval.

## Stripe Connect and email

Creator contracts, KYC/tax readiness, connected-account capability status, and payout approval must all be true before a payout may be submitted. Mail sending requires OAuth and per-message approval.
