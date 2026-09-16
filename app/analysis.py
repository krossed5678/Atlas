from __future__ import annotations
import base64, json, os
from pathlib import Path
import httpx
from PIL import Image, ImageChops, ImageStat

PROMPT = '''Return JSON only. Analyze this owner-authorized property reference photo. Include room_type, geometry, camera {height_m,fov_degrees,confidence}, lighting, materials, objects [{id,type,estimated_dimensions_m,confidence}], uncertainty. Never claim unknown measurements are exact.'''

def local_analysis(image: Path) -> dict:
    raw = base64.b64encode(image.read_bytes()).decode()
    payload={"model":os.getenv("ASTRA_OLLAMA_MODEL","qwen3-vl:4b"),"format":"json","stream":False,"messages":[{"role":"user","content":PROMPT,"images":[raw]}]}
    response=httpx.post(os.getenv("ASTRA_OLLAMA_URL","http://127.0.0.1:11434")+"/api/chat",json=payload,timeout=180)
    response.raise_for_status(); return json.loads(response.json()["message"]["content"])

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
