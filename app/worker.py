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
        property_root = PROPERTIES / job["entity_id"]
        base = property_root / "analysis"
        health = ollama_health()
        images = sorted((property_root / "source" / "original_images").glob("*"))
        cv_images=[]
        for image in images:
            try: cv_images.append({"image":image.name,"computer_vision":image_features(image)})
            except Exception as exc: cv_images.append({"image":image.name,"error":str(exc)})
        result = {"status": "cv_analyzed_awaiting_model" if not health.get("model_present") else "model_ready", "model_health": health, "generated_at": now(), "images":cv_images, "uncertainty": "Human/Astra review is required before any reconstruction is approved."}
        if health.get("model_present") and images:
            for item, image in zip(cv_images,images):
                if "error" in item: continue
                try: item["analysis"] = local_analysis(image, property_root / "analysis" / "model_cache")
                except Exception as exc: item["analysis_error"] = str(exc)
            result["status"] = "analyzed"
        successful=[item for item in cv_images if "computer_vision" in item]
        (base / "image_metadata.json").write_text(json.dumps({"generated_at":now(),"images":[{"image":item["image"],"dimensions_px":item["computer_vision"]["dimensions_px"],"image_quality":item["computer_vision"]["image_quality"]} for item in successful]},indent=2))
        (base / "camera_estimates.json").write_text(json.dumps({"generated_at":now(),"estimates":[{"image":item["image"],**item["computer_vision"]["camera_estimate"]} for item in successful]},indent=2))
        (base / "material_estimates.json").write_text(json.dumps({"generated_at":now(),"estimates":[{"image":item["image"],**item["computer_vision"]["material_color_estimate"]} for item in successful]},indent=2))
        (base / "geometry_estimates.json").write_text(json.dumps({"generated_at":now(),"estimates":[{"image":item["image"],"line_segments":item["computer_vision"]["line_segments"],"uncertainty":item["computer_vision"]["uncertainty"]} for item in successful]},indent=2))
        (base / "room_classification.json").write_text(json.dumps(result, indent=2))
        c.execute("update jobs set status='completed', checkpoint='cv_and_model_analysis_complete', updated_at=? where id=?", (now(), job["id"])); c.commit()
        audit("job.completed", "job", job["id"], result)
        return result
    except Exception as exc:
        c.execute("update jobs set status='failed', error=?, updated_at=? where id=?", (str(exc), now(), job["id"])); c.commit(); audit("job.failed", "job", job["id"], {"error": str(exc)}); raise
    finally: c.close()

if __name__ == "__main__": print(json.dumps(process_one(), indent=2))
