from __future__ import annotations
import base64, hashlib, io, json, os
from pathlib import Path
import httpx
from PIL import Image, ImageChops, ImageStat

PROMPT = '''JSON only: room_type; geometry; camera{height_m,fov_degrees,confidence}; lighting; materials; objects[{id,type,estimated_dimensions_m,confidence}]; uncertainty. Estimates need confidence; never state unknown scale as fact.'''

def compact_image(image: Path) -> tuple[str, str]:
    """Downscale/compress vision input before base64 encoding to reduce VRAM and request size."""
    max_edge=int(os.getenv("ASTRA_OLLAMA_MAX_IMAGE_EDGE","1024"))
    quality=int(os.getenv("ASTRA_OLLAMA_JPEG_QUALITY","82"))
    with Image.open(image) as source:
        source=source.convert("RGB")
        source.thumbnail((max_edge,max_edge))
        buffer=io.BytesIO();source.save(buffer,format="JPEG",quality=quality,optimize=True)
    raw=buffer.getvalue(); fingerprint=hashlib.sha256(raw+PROMPT.encode()).hexdigest()
    return base64.b64encode(raw).decode(),fingerprint

def local_analysis(image: Path, cache_dir: Path | None = None) -> dict:
    raw, fingerprint = compact_image(image)
    cache_path=(cache_dir/f"{fingerprint}.json") if cache_dir else None
    if cache_path and cache_path.is_file(): return json.loads(cache_path.read_text())
    payload={"model":os.getenv("ASTRA_OLLAMA_MODEL","qwen3-vl:4b"),"format":"json","stream":False,"keep_alive":os.getenv("ASTRA_OLLAMA_KEEP_ALIVE","0"),"options":{"num_ctx":int(os.getenv("ASTRA_OLLAMA_CONTEXT_TOKENS","2048")),"num_predict":int(os.getenv("ASTRA_OLLAMA_MAX_OUTPUT_TOKENS","600")),"temperature":0.1},"messages":[{"role":"user","content":PROMPT,"images":[raw]}]}
    response=httpx.post(os.getenv("ASTRA_OLLAMA_URL","http://127.0.0.1:11434")+"/api/chat",json=payload,timeout=180)
    response.raise_for_status(); result=json.loads(response.json()["message"]["content"])
    if cache_path:
        cache_dir.mkdir(parents=True,exist_ok=True);cache_path.write_text(json.dumps(result,indent=2))
    return result

def openai_analysis(image: Path) -> dict:
    key=os.getenv("ASTRA_OPENAI_API_KEY")
    if not key: raise RuntimeError("ASTRA_OPENAI_API_KEY is not configured")
    from openai import OpenAI
    encoded=base64.b64encode(image.read_bytes()).decode()
    client=OpenAI(api_key=key)
    response=client.responses.create(model=os.getenv("ASTRA_OPENAI_MODEL","gpt-6-astra"),store=False,input=[{"role":"user","content":[{"type":"input_text","text":PROMPT},{"type":"input_image","image_url":f"data:image/jpeg;base64,{encoded}","detail":"high"}]}])
    return json.loads(response.output_text)

def reference_score(reference: Path, rendered: Path) -> dict:
    a=Image.open(reference).convert("RGB").resize((512,512)); b=Image.open(rendered).convert("RGB").resize((512,512))
    diff=ImageStat.Stat(ImageChops.difference(a,b)).mean
    color=max(0,100-(sum(diff)/3/255*100)); return {"score":round(color,2),"color":round(color,2),"geometry":None,"camera":None,"materials":None,"lighting":None,"note":"Geometry/camera require calibrated scene render and model evidence."}
