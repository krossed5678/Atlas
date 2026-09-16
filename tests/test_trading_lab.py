import csv

from fastapi.testclient import TestClient

from app.main import app

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
