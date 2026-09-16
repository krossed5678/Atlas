import csv
import json
import uuid

from fastapi.testclient import TestClient

from app.main import app, connect, now

client = TestClient(app)


def test_research_evolution_is_held_out_and_never_live(tmp_path):
    folder = tmp_path / "bars"
    folder.mkdir()
    with (folder / "SPY__etf.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["timestamp", "close"])
        writer.writeheader()
        for index in range(180):
            writer.writerow({"timestamp": f"2025-01-{index + 1:03d}", "close": 100 + index * .1 + (index % 7) * .2})
    imported = client.post("/api/trading/import-bars", json={"folder_path": str(folder)})
    assert imported.status_code == 200
    result = client.post("/api/trading/evolve", json={"symbol": "SPY", "population_size": 12, "generations": 2, "seed": 1})
    assert result.status_code == 200
    report = result.json()["report"]
    assert report["mode"] == "RESEARCH_ONLY"
    assert report["live_trading_allowed"] is False
    assert report["data_partitions"]["train"][1] < report["data_partitions"]["validation"][1] < report["data_partitions"]["test"][1]
    assert report["efficiency"]["rolling_statistics"] == "prefix_sum_vectorized"
    assert report["walk_forward"]["fold_count"] == 3
    assert report["market_regime"]["latest_regime"] in {"risk_on","risk_off","high_volatility"}


def test_universe_evolution_processes_imported_asset_classes(tmp_path):
    folder = tmp_path / "universe"
    folder.mkdir()
    for filename in ("QQQ__etf.csv", "BTCUSD__crypto.csv"):
        with (folder / filename).open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["timestamp", "close"])
            writer.writeheader()
            for index in range(100): writer.writerow({"timestamp": str(index), "close": 100 + index})
    assert client.post("/api/trading/import-bars", json={"folder_path": str(folder)}).status_code == 200
    result = client.post("/api/trading/evolve-universe", json={"population_size": 8, "generations": 1, "asset_classes": ["etf", "crypto"]})
    assert result.status_code == 200
    body = result.json()
    assert body["mode"] == "RESEARCH_ONLY" and body["series_processed"] == 2
    strategies = client.get("/api/trading/strategies", params={"status": "PAPER_CANDIDATE"}).json()
    assert strategies["mode"] == "RESEARCH_ONLY"
    assert all(item["summary"]["mode"] == "RESEARCH_ONLY" for item in strategies["strategies"])


def test_bot_reader_position_lifecycle_deletes_cache_on_close(tmp_path):
    folder = tmp_path / "lifecycle"; folder.mkdir()
    with (folder / "IWM__etf.csv").open("w", newline="") as handle:
        writer=csv.DictWriter(handle, fieldnames=["timestamp", "close"]); writer.writeheader()
        for index in range(100): writer.writerow({"timestamp":str(index),"close":100 + index})
    assert client.post("/api/trading/import-bars",json={"folder_path":str(folder)}).status_code == 200
    c=connect(); ids=[]
    for role in ("market_reader", "trader"):
        ident=str(uuid.uuid4()); ids.append(ident)
        report={"candidate":{"fast":3,"slow":20,"entry_z":-100,"exit_z":-101}}
        c.execute("insert into strategies values (?,?,?,?,?,?,?)",(ident,"IWM","etf",role,"PAPER_CANDIDATE",json.dumps(report),now()))
    c.commit(); c.close()
    reader=client.post("/api/trading/bots",json={"strategy_id":ids[0],"role":"market_reader"}).json()
    trader=client.post("/api/trading/bots",json={"strategy_id":ids[1],"role":"trader"}).json()
    snapshot=client.post("/api/trading/market-snapshots",json={"reader_bot_id":reader["id"],"symbol":"IWM"}).json()
    opened=client.post(f"/api/trading/bots/{trader['id']}/cycle",json={"notional_cents":10000})
    assert opened.json()["action"] == "OPENED_PAPER_POSITION"
    c=connect(); c.execute("update strategies set report=? where id=?",(json.dumps({"candidate":{"fast":3,"slow":20,"entry_z":100,"exit_z":99}}),ids[1])); c.commit(); c.close()
    closed=client.post(f"/api/trading/bots/{trader['id']}/cycle",json={"notional_cents":10000})
    assert closed.json()["action"] == "CLOSED_PAPER_POSITION" and closed.json()["cache_deleted"] is True
    c=connect(); assert c.execute("select * from market_cache where id=?",(snapshot["id"],)).fetchone() is None; c.close()
