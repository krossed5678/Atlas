"""Run manually after `ollama pull qwen3-vl:4b`; writes no repository files."""
import json
from pathlib import Path
from app.analysis import local_analysis

print(json.dumps(local_analysis(Path('data/smoke-room.jpg')), indent=2))
