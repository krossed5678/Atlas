# Security and external-action policy

All integrations start disabled. Credentials must be supplied through environment variables or the Windows credential store, never source code. Every external write requires a distinct human approval record and idempotency key. The trading service never unlocks live trading: only an external official Robinhood authorization plus human approval can produce a handoff package.

Local model weights reside under `C:\Users\koanr\.ollama\models` and are excluded by `.gitignore` because they are machine-local artifacts, not source code.
