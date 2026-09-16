"""Local, paper-only evolutionary strategy research.

It consumes normalized OHLCV CSV files written by an approved market-data adapter.
No function in this module talks to a broker or can submit an order.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import random
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np

SUPPORTED_ASSET_CLASSES = {"stock", "etf", "crypto"}


@dataclass(frozen=True)
class Candidate:
    fast: int
    slow: int
    entry_z: float
    exit_z: float


def load_bars(path: Path) -> list[dict]:
    """Read `timestamp,close` (plus optional OHLCV fields), rejecting malformed series."""
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) < 90 or not {"timestamp", "close"}.issubset(rows[0] if rows else {}):
        raise ValueError(f"{path.name}: requires at least 90 timestamp/close rows")
    parsed = [{**row, "close": float(row["close"])} for row in rows]
    if any(row["close"] <= 0 for row in parsed):
        raise ValueError(f"{path.name}: close must be positive")
    return parsed


def strategy_returns(closes: np.ndarray, candidate: Candidate, fee_bps: float, slippage_bps: float) -> np.ndarray:
    returns = np.diff(closes) / closes[:-1]
    signal = np.zeros(len(returns))
    # Prefix sums replace repeated NumPy slices/means/stds for every candidate.
    cumulative=np.concatenate(([0.0],np.cumsum(returns)))
    cumulative_sq=np.concatenate(([0.0],np.cumsum(returns*returns)))
    indexes=np.arange(candidate.slow,len(returns))
    baseline=(cumulative[indexes]-cumulative[indexes-candidate.slow])/candidate.slow
    fast=(cumulative[indexes]-cumulative[indexes-candidate.fast])/candidate.fast
    variance=np.maximum(1e-18,(cumulative_sq[indexes]-cumulative_sq[indexes-candidate.slow])/candidate.slow-baseline*baseline)
    z_scores=(fast-baseline)/np.sqrt(variance)
    for index,z in zip(indexes,z_scores):
        signal[index] = 1.0 if z >= candidate.entry_z else (0.0 if z <= candidate.exit_z else signal[index - 1])
    turnover = np.abs(np.diff(signal, prepend=0.0))
    costs = turnover * (fee_bps + slippage_bps) / 10_000
    return signal * returns - costs


def metrics(returns: np.ndarray) -> dict[str, float | int]:
    if not len(returns):
        return {"total_return": 0.0, "sharpe": 0.0, "max_drawdown": 0.0, "trades": 0}
    equity = np.cumprod(1 + returns)
    high = np.maximum.accumulate(equity)
    drawdown = float(np.min(equity / high - 1))
    sd = float(np.std(returns))
    sharpe = float(np.mean(returns) / sd * math.sqrt(252)) if sd else 0.0
    return {"total_return": float(equity[-1] - 1), "sharpe": sharpe, "max_drawdown": drawdown, "trades": int(np.count_nonzero(returns))}


def score(candidate: Candidate, closes: np.ndarray, fee_bps: float, slippage_bps: float) -> tuple[float, dict]:
    report = metrics(strategy_returns(closes, candidate, fee_bps, slippage_bps))
    return float(report["sharpe"] + report["total_return"] * 2 + report["max_drawdown"] * 3), report


def evolve(closes: np.ndarray, population_size: int = 512, generations: int = 20, seed: int = 7, fee_bps: float = 5, slippage_bps: float = 5, patience: int = 5) -> dict:
    """Evolve a reproducible population on train only; validate/test are held out."""
    if population_size < 8 or generations < 1:
        raise ValueError("population_size >= 8 and generations >= 1")
    randomizer = random.Random(seed)
    train_end, validation_end = int(len(closes) * .60), int(len(closes) * .80)
    train, validation, test = closes[:train_end], closes[train_end:validation_end], closes[validation_end:]
    population = [Candidate(randomizer.randint(3, 15), randomizer.randint(20, 80), round(randomizer.uniform(.1, 2.0), 2), round(randomizer.uniform(-2.0, -.05), 2)) for _ in range(population_size)]
    history=[]
    best_seen=-float("inf"); stagnant=0
    for generation in range(generations):
        ranked = sorted(((score(c, train, fee_bps, slippage_bps)[0], c) for c in population), reverse=True, key=lambda item:item[0])
        parents = [candidate for _, candidate in ranked[:max(4, population_size // 8)]]
        history.append({"generation": generation + 1, "best_train_score": ranked[0][0]})
        if ranked[0][0] > best_seen + 1e-9: best_seen=ranked[0][0];stagnant=0
        else: stagnant += 1
        if stagnant >= patience:
            history[-1]["early_stop"]="no_train_improvement"
            population=[candidate for _,candidate in ranked]
            break
        next_population = parents[:]
        while len(next_population) < population_size:
            parent = randomizer.choice(parents)
            fast = max(2, min(20, parent.fast + randomizer.choice([-2, -1, 0, 1, 2])))
            slow = max(fast + 5, min(100, parent.slow + randomizer.choice([-8, -4, 0, 4, 8])))
            next_population.append(Candidate(fast, slow, round(max(.05, parent.entry_z + randomizer.uniform(-.3, .3)), 2), round(min(-.01, parent.exit_z + randomizer.uniform(-.3, .3)), 2)))
        population = next_population
    champion = max(population, key=lambda candidate: score(candidate, train, fee_bps, slippage_bps)[0])
    train_score, train_metrics = score(champion, train, fee_bps, slippage_bps)
    _, validation_metrics = score(champion, validation, fee_bps, slippage_bps)
    _, test_metrics = score(champion, test, fee_bps, slippage_bps)
    promoted = bool(validation_metrics["sharpe"] > 0 and test_metrics["sharpe"] > 0 and validation_metrics["max_drawdown"] >= -.20 and test_metrics["max_drawdown"] >= -.20)
    return {"candidate": asdict(champion), "training": train_metrics, "validation": validation_metrics, "test": test_metrics, "train_score": train_score, "promoted_to_paper_candidate": promoted, "history": history, "data_partitions": {"train": [0, train_end], "validation": [train_end, validation_end], "test": [validation_end, len(closes)]}, "cost_model": {"fee_bps": fee_bps, "slippage_bps": slippage_bps},"efficiency":{"requested_generations":generations,"executed_generations":len(history),"early_stop_patience":patience,"rolling_statistics":"prefix_sum_vectorized"}}


def manifest_entry(path: Path, asset_class: str, symbol: str) -> dict:
    if asset_class not in SUPPORTED_ASSET_CLASSES:
        raise ValueError("asset_class must be stock, etf, or crypto")
    return {"symbol": symbol.upper(), "asset_class": asset_class, "path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def save_result(directory: Path, symbol: str, result: dict) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    destination = directory / f"{symbol.upper()}-evolution.json"
    destination.write_text(json.dumps(result, indent=2))
    return destination


def current_signal(closes: np.ndarray, candidate: Candidate) -> str:
    """Return a deterministic long/flat decision from the latest completed price bar."""
    if len(closes) <= candidate.slow + 1:
        return "flat"
    returns = np.diff(closes) / closes[:-1]
    window = returns[-candidate.slow:]
    fast_mean = float(np.mean(window[-candidate.fast:]))
    baseline = float(np.mean(window))
    deviation = float(np.std(window)) or 1e-9
    z = (fast_mean - baseline) / deviation
    return "long" if z >= candidate.entry_z else "flat"
