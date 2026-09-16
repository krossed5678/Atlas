"""Checkpointed local worker. It deliberately performs no external write actions."""
from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path

import httpx

from .main import DATA, PROPERTIES, audit, init_db, now
from .analysis import local_analysis
from .vision import image_features

DB = DATA / "astra.db"

def ollama_health() -> dict:
    try:
        response = httpx.get(os.getenv("ASTRA_OLLAMA_URL", "http://127.0.0.1:11434") + "/api/tags", timeout=5)
        response.raise_for_status()
        models = [m.get("name") for m in response.json().get("models", [])]
        return {"reachable": True, "model_present": os.getenv("ASTRA_OLLAMA_MODEL", "qwen3-vl:4b") in models, "models": models}
    except Exception as exc:
        return {"reachable": False, "error": str(exc)}

def process_one() -> dict | None:
    init_db()
    c = sqlite3.connect(DB); c.row_factory = sqlite3.Row
    job = c.execute("select * from jobs where status='queued' order by created_at limit 1").fetchone()
    if not job: c.close(); return None
    c.execute("update jobs set status='running', attempts=attempts+1, updated_at=? where id=?", (now(), job["id"])); c.commit()
    try:
        if job["kind"] != "property_analysis": raise RuntimeError("Unknown job kind")
        base = PROPERTIES / job["entity_id"] / "analysis"
        health = ollama_health()
        images = sorted((PROPERTIES / job["entity_id"] / "source" / "original_images").glob("*"))
        result = {"status": "awaiting_model" if not health.get("model_present") else "model_ready", "model_health": health, "generated_at": now(), "uncertainty": "Human/Astra review is required before any reconstruction is approved."}
        if health.get("model_present") and images:
            result["images"] = [{"image": image.name, "computer_vision": image_features(image), "analysis": local_analysis(image)} for image in images]
            result["status"] = "analyzed"
        (base / "room_classification.json").write_text(json.dumps(result, indent=2))
        c.execute("update jobs set status='completed', checkpoint='analysis_placeholder_complete', updated_at=? where id=?", (now(), job["id"])); c.commit()
        audit("job.completed", "job", job["id"], result)
        return result
    except Exception as exc:
        c.execute("update jobs set status='failed', error=?, updated_at=? where id=?", (str(exc), now(), job["id"])); c.commit(); audit("job.failed", "job", job["id"], {"error": str(exc)}); raise
    finally: c.close()

if __name__ == "__main__": print(json.dumps(process_one(), indent=2))
