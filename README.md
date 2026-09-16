# ASTRA Local Operations Platform

Local-first control plane for authorized property visualizations, Shopify/TikTok creator operations, and paper/shadow trading.

## Current verified state — 2026-09-16

- GitHub repository: `https://github.com/krossed5678/Atlas.git` (`main`).
- Python 3.12, Blender 5.2.1, FFmpeg, Ollama 0.34.1, and BrowserAct 1.4.2 are installed locally.
- The `qwen3-vl:4b` download is active in `C:\Users\koanr\.ollama\models`; it is intentionally not stored in this repository.
- The local dashboard is served at `http://127.0.0.1:8787`, and `ASTRA Local Safe Worker` runs every 15 minutes with external writes disabled.
- Run `python -m pytest -q` from the virtual environment to run the current five-test safety suite.

Read [INTEGRATIONS.md](INTEGRATIONS.md) before connecting an external account; the repository intentionally contains no credentials.

## Run

1. Run `setup.ps1` in PowerShell.
2. Run `start.ps1`.
3. Open `http://127.0.0.1:8787`.

All external write adapters are disabled by default. See `WHATISLEFT.md` for activation dependencies and verification evidence.
