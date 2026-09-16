# Trading Research Design Notes

ASTRA deliberately keeps its paper-first engine lightweight. It borrows durable
design ideas rather than importing a large training stack into a 4 GB GPU machine.

## Implemented

- Versioned strategy reports with a SHA-256 fingerprint of the exact price-bar input.
- Chronological train/validation/test separation and sequential out-of-sample walk-forward folds.
- Fee and slippage model in every evaluation.
- Multi-criterion paper-candidate gate: positive held-out scores, controlled drawdown, and a majority of profitable walk-forward folds.
- Regime summary and deterministic early stopping.

## External references evaluated

- Microsoft Qlib: modular data, research, model, risk, and execution architecture.
- AI4Finance FinRL / FinRL-Meta: market environments, agent layer, and realistic data/environment separation.
- MLflow Model Registry: experiment lineage and versioned model lifecycle.

These are reference architectures, not endorsements or proof that a strategy is profitable. They remain optional integrations until a compatible complete market-data feed is available.
