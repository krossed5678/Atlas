# ASTRA Local Operations Platform

Local-first control plane for authorized property visualizations, Shopify/TikTok creator operations, and paper/shadow trading.

## Current verified state — 2026-09-16

- GitHub repository: `https://github.com/krossed5678/Atlas.git` (`main`).
- Python 3.12, Blender 5.2.1, FFmpeg, Ollama 0.34.1, and BrowserAct 1.4.2 are installed locally.
- `qwen3-vl:4b` is installed in `C:\Users\koanr\.ollama\models`; a real synthetic-room vision smoke test returned structured scene JSON successfully. It is intentionally not stored in this repository.
- The local dashboard is served at `http://127.0.0.1:8787`, and `ASTRA Local Safe Worker` runs every 15 minutes with external writes disabled.
- Run `python -m pytest -q` from the virtual environment to run the current eight-test safety suite.

## Evolutionary Trading Research

`POST /api/trading/import-bars` accepts a local folder of normalized price-bar CSV files named `SYMBOL__stock.csv`, `SYMBOL__etf.csv`, or `SYMBOL__crypto.csv`. Each file requires `timestamp,close` and at least 90 rows. `POST /api/trading/evolve` evolves a default population of 512 parameterized research agents on only the first 60% of each series, evaluates the winner on the next 20%, and reports final held-out performance on the last 20% after fees and slippage.

`POST /api/trading/evolve-universe` applies the same isolated workflow to every imported series, optionally filtered by asset class. It writes a separate versioned experiment per instrument; a winning result is never pooled into another asset class and is never a trade authorization.

The local model may analyze journals and market context, but cannot modify risk limits, the data partitions, promotion criteria, allocation, or order permissions. A successful candidate is only a `PAPER_CANDIDATE`; no endpoint in this research component talks to Robinhood or creates an order.

The dashboard now supports selecting qualified strategies as paper bots. One selected `market_reader` bot can cache a latest normalized price snapshot locally; trader bots use that snapshot to open, monitor, and close paper positions. When a paper position closes, its linked market-cache record is permanently deleted while the position event remains in the audit trail.

## Computer Vision Property Analysis

Property jobs now calculate image dimensions, edge density, perspective line segments, horizontal/vertical evidence, brightness, saturation, color signals, and uncertainty before sending the image to the local Qwen vision model. `reconstruction_score` compares a Blender render against a reference using structural similarity, edge overlap, and color similarity. These are measurement aids, not guarantees of architectural accuracy.

## Luxury Promo Exports

One click now produces a finished 1080p luxury landscape promo or a 1080×1920 vertical TikTok promo. The editor creates a CV-ranked shot sequence, alternating slow push/pull/drift movement, subtle warm color finishing, sharpening, fades, and motion cross-dissolves. It uses only the supplied photographs and does not invent property features. Music is deliberately omitted unless you provide a licensed track.

Read [INTEGRATIONS.md](INTEGRATIONS.md) before connecting an external account; the repository intentionally contains no credentials.

## Run

1. Run `setup.ps1` in PowerShell.
2. Run `start.ps1`.
3. Open `http://127.0.0.1:8787`.

All external write adapters are disabled by default. See `WHATISLEFT.md` for activation dependencies and verification evidence.
