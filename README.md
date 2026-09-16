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

The local model may analyze journals and market context, but cannot modify risk limits, the data partitions, promotion criteria, allocation, or order permissions. A successful candidate is only a `PAPER_CANDIDATE`; no endpoint in this research component talks to Robinhood or creates an order.

Read [INTEGRATIONS.md](INTEGRATIONS.md) before connecting an external account; the repository intentionally contains no credentials.

## Run

1. Run `setup.ps1` in PowerShell.
2. Run `start.ps1`.
3. Open `http://127.0.0.1:8787`.

All external write adapters are disabled by default. See `WHATISLEFT.md` for activation dependencies and verification evidence.
