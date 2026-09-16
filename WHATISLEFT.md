# ASTRA Build Status

Last updated: 2026-09-16

Repository: `https://github.com/krossed5678/Atlas.git` (`main`)

## BUILT AND VERIFIED

- Python 3.12, FastAPI, SQLite persistence, immutable audit events, local dashboard, emergency stop, and the 15-minute `ASTRA Local Safe Worker` are installed and working locally. The worker runs as a hidden background scheduled task, logs to `data/logs/scheduled-worker.log`, and does not attach to interactive/fullscreen terminals.
- Blender 5.2.1 headless scene-file smoke test passed. FFmpeg installation reported success.
- Ollama 0.34.1 and `qwen3-vl:4b` are installed. The model lives at `C:\Users\koanr\.ollama\models`; a real local synthetic-room vision run returned structured room, camera, material, object, confidence, and uncertainty JSON.
- User-supplied photo folders can be imported into the per-property project structure and queued for analysis. Upload intake is also available in the dashboard.
- OpenCV and scikit-image computer vision are installed and used by the queued property worker for perspective-line, image-quality, color/material evidence, and reference/render scoring. The worker persistently writes image metadata, camera, material, and geometry analysis JSON before layering Qwen analysis on top.
- Thirteen automated safe-mode tests pass, including duplicate/idempotency protection, capital and live-gate safety, property-folder CV analysis, FFmpeg video rendering, paper-bot lifecycle/cache deletion, strategy evolution, and TikTok readiness gating.
- Cinematic photo-promo rendering is implemented and verified with FFmpeg: photo-set storyboard, slow push-in shots, MP4 generation, and one-click dashboard render. It uses supplied images only.
- Local evolutionary Trading Lab is implemented for normalized stock, ETF, and crypto price bars. It evolves 512 parameterized research agents by default, models fees/slippage, enforces train/validation/test separation, stores versioned per-instrument reports, and can promote only to a paper candidate.
- Paper bot dashboard and lifecycle are implemented: select a held-out candidate, designate one market reader, cache a local snapshot, open/monitor/close simulated positions, and permanently delete the cache attached to a closed position.
- The configured default Shopify store is `x6qufc-nh.myshopify.com` (USD, EDT). Plan: trial — you'll need to upgrade before you can start selling and unlock full features
- Kofi Rossi Stripe account selection is recorded as `acct_1SPAFpI0vp8qwDso` in **test mode**. Creator money flow is configured conceptually as a Stripe Connect Accounts v2 marketplace recipient flow with separate charges/transfers and individual human approval for every payout.
- Robinhood's official `robinhood-trading` MCP is registered in Codex. OAuth was approved and a privacy-minimized account check succeeded; no balances, positions, account numbers, or orders were recorded. ASTRA's live-trading gate remains locked.
- Git repository is initialized and pushed. Secrets, model files, logs, database state, and virtual environments are excluded.

## BUILT BUT NOT VERIFIED

- Queue worker, local Qwen structured-analysis adapter, Blender starter scene builder, camera/material score scaffold, and reference-score scaffold.
- Local dashboard schemas for leads, creators, contracts, payouts, ledgers, and paper/shadow trade proposals. External-write settings remain false.
- A Robinhood market-data ingestion adapter is not yet present. The Trading Lab accepts normalized local price bars now; the official Robinhood MCP is not used by this local service to fetch a whole-market universe.
- Stripe Connect configuration hooks select the Kofi Rossi test account without embedding a secret. The implementation design uses Accounts v2 and does not use legacy connected-account types.
- Shopify selection hook uses the connected default store. Live catalog/order synchronization has not been exercised from this local service.
- TikTok Shop readiness endpoint and OAuth configuration gate are implemented; merchant API calls, catalog ingestion, order handling, and fulfillment require the official credentials and merchant authorization.
- OpenAI, TikTok Shop, mailbox, Stripe, and Robinhood adapters have safe readiness checks but are not yet end-to-end service integrations.

## REQUIRES YOUR AUTHORIZATION

- A local OpenAI API key, mailbox OAuth authorization, TikTok Shop/business app authorization, and the appropriate Shopify Admin app/access token for the local service.
- Stripe Connect live-mode activation requires Kofi Rossi live-mode selection, Connect platform configuration, connected-creator onboarding, tax/legal review, webhook endpoint registration, and a specific payout approval. Test mode is selected now; no payout was created.
- Shopify stays on its current trial at your direction. Shopify live selling/order verification is deferred; TikTok Shop can be the first commerce path once its business authorization and catalog/fulfillment configuration are connected.
- Robinhood stock/options automation requires a separate explicit live-order instruction per order and any product-level authorization Robinhood requires. The verified Agentic MCP connection does not unlock ASTRA's hard gate.

## NOT POSSIBLE WITH CURRENT INTEGRATIONS

- A true 1:1 property reconstruction cannot be guaranteed from arbitrary photos; ASTRA reports measured scores and uncertainty instead.
- Fully unattended creator payouts, public TikTok publishing, outbound email, or Robinhood orders are intentionally not possible: each requires the configured platform connection and a distinct approval action.

## NEXT BUILD CHECKPOINTS

- [x] Import user-supplied photo folders into persistent property projects.
- [x] Pull and smoke-test `qwen3-vl:4b`.
- [x] Install and smoke-test Blender.
- [x] Register and verify Robinhood Agentic MCP with a privacy-minimized account read.
- [x] Select Kofi Rossi Stripe test context and default Shopify store in non-secret configuration.
- [ ] Run a complete supplied-photo-folder-to-cinematic-promotional-video job using an actual property folder.
- [ ] Build and verify Shopify order/catalog webhooks, TikTok Shop sync, creator attribution, approved calendar publishing, and refund reconciliation.
- [ ] Build and verify Stripe Connect test onboarding, webhook verification, creator statement generation, and payout-approval handoff; do not enable live mode until the live prerequisites above are complete.
- [ ] Connect an approved mailbox and implement reviewed send/reply/bounce workflows.
- [ ] Add and verify OpenAI high-fidelity property-analysis calls after an API key is present.
- [ ] Expand the paper/shadow trading engine with real market-data adapters, historical partitions, strategy metrics, and Robinhood live-handoff packages.
- [ ] Add an authorized Robinhood market-data adapter, define the available stock/ETF/crypto universe and rate limits, ingest fresh bars, and run rolling paper/shadow evaluation. “All instruments” cannot be claimed until that data source is available and complete.
- [ ] Run the remaining synthetic matrix: corrupt/missing images, Blender restart, score regression, bounces, attribution conflicts, holdbacks, failed Stripe payout, unapproved post, stale data, partial fills, and circuit breakers.
