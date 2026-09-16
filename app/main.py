from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

import numpy as np

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from app.integrations import commerce_configuration, readiness
from app.trading_lab import SUPPORTED_ASSET_CLASSES, evolve, load_bars, manifest_entry, save_result

ROOT = Path(__file__).resolve().parents[1]
DATA = Path(os.getenv("ASTRA_DATA_DIR", ROOT / "data"))
PROPERTIES = DATA / "properties"
STATIC = ROOT / "web"
DB = DATA / "astra.db"

app = FastAPI(title="ASTRA Local Operations Platform", version="0.1.0")
app.mount("/static", StaticFiles(directory=STATIC), name="static")


def now() -> str:
    return datetime.now(UTC).isoformat()


def connect() -> sqlite3.Connection:
    DATA.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(DB, timeout=10)
    c.row_factory = sqlite3.Row
    return c


def init_db() -> None:
    c = connect()
    c.executescript("""
    create table if not exists events (id text primary key, at text, actor text, action text, entity_type text, entity_id text, correlation_id text, payload text);
    create table if not exists settings (key text primary key, value text not null);
    create table if not exists properties (id text primary key, listing_url text, listing_hash text unique, status text, created_at text, source_count integer default 0, score real default 0);
    create table if not exists jobs (id text primary key, kind text, entity_id text, status text, checkpoint text, attempts integer default 0, error text, created_at text, updated_at text);
    create table if not exists leads (id text primary key, email text unique, stage text, opted_out integer default 0, last_contact_at text, created_at text);
    create table if not exists creators (id text primary key, name text, email text unique, status text, created_at text);
    create table if not exists contracts (id text primary key, creator_id text, terms text, approval_required integer default 1, active integer default 0, created_at text);
    create table if not exists ledger (id text primary key, kind text, amount_cents integer, source text, reference_id text unique, created_at text);
    create table if not exists payouts (id text primary key, creator_id text, amount_cents integer, status text, statement text, created_at text);
    create table if not exists trades (id text primary key, mode text, symbol text, side text, quantity real, price real, status text, idempotency_key text unique, created_at text);
    create table if not exists market_series (symbol text primary key, asset_class text, path text, sha256 text, rows integer, imported_at text);
    create table if not exists strategies (id text primary key, symbol text, asset_class text, version text, status text, report text, created_at text);
    """)
    defaults = {"emergency_stop": "false", "trading_mode": "PAPER", "live_trading_allowed": "false", "external_writes_enabled": "false", "max_daily_loss_cents": "2500", "max_position_cents": "5000"}
    for key, value in defaults.items():
        c.execute("insert or ignore into settings(key,value) values (?,?)", (key, value))
    c.commit(); c.close()


def audit(action: str, entity_type: str, entity_id: str, payload: dict, actor: str = "local-user", correlation_id: str | None = None) -> None:
    c = connect()
    c.execute("insert into events values (?,?,?,?,?,?,?,?)", (str(uuid.uuid4()), now(), actor, action, entity_type, entity_id, correlation_id or str(uuid.uuid4()), json.dumps(payload, sort_keys=True)))
    c.commit(); c.close()


def setting(key: str) -> str:
    c = connect(); row = c.execute("select value from settings where key=?", (key,)).fetchone(); c.close()
    return row[0] if row else ""


def set_setting(key: str, value: str) -> None:
    c = connect(); c.execute("insert into settings(key,value) values (?,?) on conflict(key) do update set value=excluded.value", (key, value)); c.commit(); c.close()
    audit("setting.changed", "setting", key, {"value": value})


class LeadIn(BaseModel):
    email: str

class CreatorIn(BaseModel):
    name: str
    email: str

class ContractIn(BaseModel):
    creator_id: str
    terms: dict = Field(description="Per-creator, reviewed contract terms; no payouts are automatic.")

class LedgerIn(BaseModel):
    kind: Literal["revenue", "refund", "expense", "chargeback"]
    amount_cents: int
    reference_id: str
    source: str = "manual"

class TradeIn(BaseModel):
    symbol: str
    side: Literal["buy", "sell"]
    quantity: float = Field(gt=0)
    price: float = Field(gt=0)
    mode: Literal["RESEARCH", "PAPER", "SHADOW", "LIVE_READY_HANDOFF"] = "PAPER"
    idempotency_key: str

class FolderImportIn(BaseModel):
    folder_path: str
    listing_url: str = ""

class MarketFolderIn(BaseModel):
    folder_path: str

class EvolutionIn(BaseModel):
    symbol: str
    population_size: int = Field(default=512, ge=8, le=4096)
    generations: int = Field(default=20, ge=1, le=200)
    seed: int = 7

class UniverseEvolutionIn(BaseModel):
    population_size: int = Field(default=512, ge=8, le=4096)
    generations: int = Field(default=20, ge=1, le=200)
    seed: int = 7
    asset_classes: list[Literal["stock", "etf", "crypto"]] | None = None


@app.on_event("startup")
def startup() -> None:
    init_db(); PROPERTIES.mkdir(parents=True, exist_ok=True)


@app.get("/")
def home(): return FileResponse(STATIC / "index.html")

@app.get("/api/system")
def system():
    c = connect()
    counts = {table: c.execute(f"select count(*) from {table}").fetchone()[0] for table in ("properties", "jobs", "leads", "creators", "payouts", "trades")}
    settings = {r["key"]: r["value"] for r in c.execute("select * from settings")}
    c.close()
    return {"counts": counts, "settings": settings, "ollama_configured": bool(os.getenv("ASTRA_OLLAMA_URL", "http://127.0.0.1:11434")), "external_writes_enabled": settings["external_writes_enabled"] == "true", "commerce": commerce_configuration(), "integrations": [item.__dict__ for item in readiness()]}

@app.post("/api/system/emergency-stop")
def emergency_stop():
    set_setting("emergency_stop", "true")
    return {"ok": True, "emergency_stop": True}

@app.post("/api/system/resume")
def resume():
    set_setting("emergency_stop", "false")
    return {"ok": True, "emergency_stop": False}

@app.post("/api/properties")
async def create_property(listing_url: str = Form(""), files: list[UploadFile] = File(...)):
    if not files: raise HTTPException(400, "At least one image is required")
    digest = hashlib.sha256((listing_url + "|" + "|".join(f.filename or "" for f in files)).encode()).hexdigest()
    c = connect(); prior = c.execute("select id from properties where listing_hash=?", (digest,)).fetchone()
    if prior: c.close(); raise HTTPException(409, f"Duplicate property: {prior['id']}")
    pid = f"property_{uuid.uuid4().hex[:12]}"; base = PROPERTIES / pid
    for rel in ("source/original_images", "analysis", "blender/assets", "blender/textures", "renders/reference_matches", "renders/final_stills", "video/shots", "video/final", "outreach/emails", "logs"):
        (base / rel).mkdir(parents=True, exist_ok=True)
    saved = 0
    for i, upload in enumerate(files):
        if not (upload.content_type or "").startswith("image/"): continue
        suffix = Path(upload.filename or "image.jpg").suffix or ".jpg"
        destination = base / "source/original_images" / f"{i:03d}{suffix.lower()}"
        with destination.open("wb") as out: shutil.copyfileobj(upload.file, out)
        saved += 1
    if not saved: raise HTTPException(400, "No valid image files supplied")
    metadata = {"property_id": pid, "listing_url": listing_url, "authorized_upload": True, "created_at": now(), "source_images": saved}
    (base / "source/metadata.json").write_text(json.dumps(metadata, indent=2))
    for name in ("image_metadata.json", "room_classification.json", "camera_estimates.json", "geometry_estimates.json", "material_estimates.json"):
        (base / "analysis" / name).write_text(json.dumps({"status": "pending_local_or_astra_analysis", "confidence": 0}, indent=2))
    c.execute("insert into properties values (?,?,?,?,?,?,?)", (pid, listing_url, digest, "INTAKE_COMPLETE", now(), saved, 0))
    jid = str(uuid.uuid4()); c.execute("insert into jobs values (?,?,?,?,?,?,?,?,?)", (jid, "property_analysis", pid, "queued", "intake", 0, None, now(), now())); c.commit(); c.close()
    audit("property.intake", "property", pid, metadata)
    return {"id": pid, "job_id": jid, "status": "INTAKE_COMPLETE"}

@app.get("/api/properties")
def list_properties():
    c = connect(); rows=[dict(r) for r in c.execute("select * from properties order by created_at desc")]; c.close(); return rows

@app.post("/api/properties/import-folder")
def import_property_folder(body: FolderImportIn):
    """Copy a user-selected local image folder into a persistent property project and queue analysis."""
    source = Path(body.folder_path).expanduser().resolve()
    if not source.is_dir(): raise HTTPException(400, "Folder does not exist")
    images = [p for p in source.iterdir() if p.is_file() and p.suffix.lower() in {'.jpg','.jpeg','.png','.webp','.tif','.tiff'}]
    if not images: raise HTTPException(400, "Folder contains no supported image files")
    digest = hashlib.sha256((str(source) + "|" + "|".join(f"{p.name}:{p.stat().st_size}" for p in images)).encode()).hexdigest()
    c = connect(); prior = c.execute("select id from properties where listing_hash=?", (digest,)).fetchone()
    if prior: c.close(); raise HTTPException(409, f"Duplicate photo set: {prior['id']}")
    pid=f"property_{uuid.uuid4().hex[:12]}"; base=PROPERTIES/pid
    for rel in ("source/original_images","analysis","blender/assets","blender/textures","renders/reference_matches","renders/final_stills","video/shots","video/final","outreach/emails","logs"):(base/rel).mkdir(parents=True,exist_ok=True)
    for index,image in enumerate(sorted(images)): shutil.copy2(image,base/"source/original_images"/f"{index:03d}{image.suffix.lower()}")
    metadata={"property_id":pid,"listing_url":body.listing_url,"source_folder":str(source),"source_images":len(images),"created_at":now()}
    (base/"source/metadata.json").write_text(json.dumps(metadata,indent=2))
    for name in ("image_metadata.json","room_classification.json","camera_estimates.json","geometry_estimates.json","material_estimates.json"):(base/"analysis"/name).write_text(json.dumps({"status":"queued","confidence":0},indent=2))
    c.execute("insert into properties values (?,?,?,?,?,?,?)",(pid,body.listing_url,digest,"INTAKE_COMPLETE",now(),len(images),0));jid=str(uuid.uuid4());c.execute("insert into jobs values (?,?,?,?,?,?,?,?,?)",(jid,"property_analysis",pid,"queued","folder_intake",0,None,now(),now()));c.commit();c.close();audit("property.folder_import","property",pid,metadata);return {"id":pid,"job_id":jid,"image_count":len(images)}

@app.post("/api/leads")
def create_lead(body: LeadIn):
    c=connect(); existing=c.execute("select * from leads where email=?", (body.email.lower(),)).fetchone()
    if existing: c.close(); raise HTTPException(409, "Duplicate contact blocked")
    ident=str(uuid.uuid4()); c.execute("insert into leads values (?,?,?,?,?,?)", (ident, body.email.lower(), "DISCOVERED", 0, None, now())); c.commit(); c.close(); audit("lead.created", "lead", ident, {"email":body.email.lower()}); return {"id":ident,"stage":"DISCOVERED"}

@app.post("/api/leads/{lead_id}/opt-out")
def opt_out(lead_id:str):
    c=connect(); c.execute("update leads set opted_out=1, stage='LOST' where id=?",(lead_id,)); c.commit(); c.close(); audit("lead.opted_out","lead",lead_id,{}); return {"ok":True}

@app.post("/api/creators")
def create_creator(body: CreatorIn):
    c=connect(); ident=str(uuid.uuid4())
    try: c.execute("insert into creators values (?,?,?,?,?)",(ident,body.name,body.email.lower(),"PENDING_CONTRACT",now())); c.commit()
    except sqlite3.IntegrityError: c.close(); raise HTTPException(409,"Duplicate creator")
    c.close(); audit("creator.created","creator",ident,body.model_dump()); return {"id":ident,"status":"PENDING_CONTRACT"}

@app.post("/api/contracts")
def create_contract(body: ContractIn):
    required={"attribution_method","commission_rule","holdback_days","refund_clawback","rights","tax_status","payout_destination"}
    missing=required-set(body.terms)
    if missing: raise HTTPException(400, f"Contract terms missing: {', '.join(sorted(missing))}")
    ident=str(uuid.uuid4()); c=connect(); c.execute("insert into contracts values (?,?,?,?,?,?)",(ident,body.creator_id,json.dumps(body.terms),1,0,now())); c.commit(); c.close(); audit("contract.created","contract",ident,body.model_dump()); return {"id":ident,"status":"PENDING_HUMAN_APPROVAL"}

@app.post("/api/ledger")
def add_ledger(body: LedgerIn):
    c=connect(); ident=str(uuid.uuid4())
    try: c.execute("insert into ledger values (?,?,?,?,?,?)",(ident,body.kind,body.amount_cents,body.source,body.reference_id,now())); c.commit()
    except sqlite3.IntegrityError: c.close(); raise HTTPException(409,"Duplicate ledger reference")
    c.close(); audit("ledger.recorded","ledger",ident,body.model_dump()); return capital_status()

@app.get("/api/ledger/capital")
def capital_status():
    c=connect(); rows=c.execute("select kind, coalesce(sum(amount_cents),0) total from ledger group by kind").fetchall(); c.close(); sums={r['kind']:r['total'] for r in rows}
    profit=max(0,sums.get('revenue',0)-sums.get('refund',0)-sums.get('chargeback',0)-sums.get('expense',0)); committed=0
    return {"realized_net_profit_cents":profit,"maximum_trading_allocation_cents":profit//4,"committed_trading_capital_cents":committed,"available_trading_capital_cents":max(0,profit//4-committed)}

@app.post("/api/trades")
def propose_trade(body: TradeIn):
    if setting("emergency_stop")=="true": raise HTTPException(423,"Emergency stop is active")
    if body.mode == "LIVE_READY_HANDOFF" and setting("live_trading_allowed") != "true": raise HTTPException(403,"Live trading gate is locked; handoff cannot become an order")
    notional=int(body.quantity*body.price*100); capital=capital_status()
    if notional > capital["available_trading_capital_cents"]: raise HTTPException(400,"25% realized-profit capital boundary blocks this trade")
    if notional > int(setting("max_position_cents")): raise HTTPException(400,"Maximum position limit blocks this trade")
    c=connect(); ident=str(uuid.uuid4())
    try: c.execute("insert into trades values (?,?,?,?,?,?,?,?,?)",(ident,body.mode,body.symbol.upper(),body.side,body.quantity,body.price,"PROPOSED" if body.mode!="PAPER" else "SIMULATED",body.idempotency_key,now())); c.commit()
    except sqlite3.IntegrityError: c.close(); raise HTTPException(409,"Duplicate order prevented")
    c.close(); audit("trade.proposed","trade",ident,body.model_dump()); return {"id":ident,"status":"SIMULATED" if body.mode=="PAPER" else "PROPOSED","notional_cents":notional}

@app.get("/api/trades")
def list_trades():
    c=connect(); rows=[dict(r) for r in c.execute("select * from trades order by created_at desc")]; c.close(); return rows

@app.post("/api/trading/import-bars")
def import_market_bars(body: MarketFolderIn):
    """Copy normalized `SYMBOL__asset_class.csv` files into the paper-research data store."""
    source = Path(body.folder_path).expanduser().resolve()
    if not source.is_dir(): raise HTTPException(400, "Market-data folder does not exist")
    files = sorted(source.glob("*.csv"))
    if not files: raise HTTPException(400, "No CSV price-bar files found")
    destination_root = DATA / "market" / "bars"; destination_root.mkdir(parents=True, exist_ok=True)
    c = connect(); imported=[]
    try:
        for file in files:
            try: symbol, asset_class = file.stem.rsplit("__", 1)
            except ValueError: raise HTTPException(400, f"{file.name}: name it SYMBOL__stock.csv, SYMBOL__etf.csv, or SYMBOL__crypto.csv")
            if asset_class not in SUPPORTED_ASSET_CLASSES: raise HTTPException(400, f"{file.name}: unsupported asset class")
            bars=load_bars(file); target=destination_root/file.name; shutil.copy2(file, target)
            entry=manifest_entry(target, asset_class, symbol)
            c.execute("insert into market_series values (?,?,?,?,?,?) on conflict(symbol) do update set asset_class=excluded.asset_class,path=excluded.path,sha256=excluded.sha256,rows=excluded.rows,imported_at=excluded.imported_at", (entry["symbol"],asset_class,entry["path"],entry["sha256"],len(bars),now()))
            imported.append({"symbol":entry["symbol"],"asset_class":asset_class,"rows":len(bars)})
        c.commit()
    finally: c.close()
    audit("market_data.imported", "market_data", str(source), {"series": imported})
    return {"mode":"RESEARCH_ONLY","imported":imported}

@app.get("/api/trading/universe")
def market_universe():
    c=connect(); rows=[dict(row) for row in c.execute("select * from market_series order by asset_class, symbol")]; c.close()
    return {"mode":"RESEARCH_ONLY","series":rows,"asset_classes":sorted(SUPPORTED_ASSET_CLASSES)}

@app.post("/api/trading/evolve")
def evolve_strategy(body: EvolutionIn):
    """Evolve candidates on held-out local data. Promotion only creates a paper candidate."""
    if setting("emergency_stop") == "true": raise HTTPException(423, "Emergency stop is active")
    c=connect(); series=c.execute("select * from market_series where symbol=?", (body.symbol.upper(),)).fetchone(); c.close()
    if not series: raise HTTPException(404, "Import normalized price bars for this symbol first")
    bars=load_bars(Path(series["path"])); closes=np.array([row["close"] for row in bars], dtype=float)
    report=evolve(closes, body.population_size, body.generations, body.seed)
    ident=str(uuid.uuid4()); status="PAPER_CANDIDATE" if report["promoted_to_paper_candidate"] else "REJECTED"
    report.update({"symbol":series["symbol"],"asset_class":series["asset_class"],"mode":"RESEARCH_ONLY","live_trading_allowed":False})
    path=save_result(DATA/"market"/"experiments",series["symbol"],report)
    c=connect(); c.execute("insert into strategies values (?,?,?,?,?,?,?)",(ident,series["symbol"],series["asset_class"],f"evo-{ident[:8]}",status,json.dumps(report),now()));c.commit();c.close()
    audit("strategy.evolved", "strategy", ident, {"symbol":series["symbol"],"status":status,"result_path":str(path)})
    return {"id":ident,"status":status,"report":report}

@app.post("/api/trading/evolve-universe")
def evolve_universe(body: UniverseEvolutionIn):
    """Run isolated research experiments across all imported instruments (no broker access)."""
    if setting("emergency_stop") == "true": raise HTTPException(423, "Emergency stop is active")
    c=connect()
    query="select * from market_series"
    values: tuple = ()
    if body.asset_classes:
        query += " where asset_class in (" + ",".join("?" for _ in body.asset_classes) + ")"
        values=tuple(body.asset_classes)
    series_rows=c.execute(query + " order by asset_class,symbol", values).fetchall(); c.close()
    if not series_rows: raise HTTPException(404, "No normalized market series have been imported")
    completed=[]
    for offset, series in enumerate(series_rows):
        bars=load_bars(Path(series["path"])); closes=np.array([row["close"] for row in bars], dtype=float)
        report=evolve(closes, body.population_size, body.generations, body.seed + offset)
        ident=str(uuid.uuid4()); status="PAPER_CANDIDATE" if report["promoted_to_paper_candidate"] else "REJECTED"
        report.update({"symbol":series["symbol"],"asset_class":series["asset_class"],"mode":"RESEARCH_ONLY","live_trading_allowed":False})
        output=save_result(DATA/"market"/"experiments",series["symbol"],report)
        c=connect(); c.execute("insert into strategies values (?,?,?,?,?,?,?)",(ident,series["symbol"],series["asset_class"],f"evo-{ident[:8]}",status,json.dumps(report),now()));c.commit();c.close()
        completed.append({"id":ident,"symbol":series["symbol"],"asset_class":series["asset_class"],"status":status,"result_path":str(output)})
    audit("strategy.universe_evolved", "strategy_batch", str(uuid.uuid4()), {"count":len(completed),"asset_classes":body.asset_classes or sorted(SUPPORTED_ASSET_CLASSES)})
    return {"mode":"RESEARCH_ONLY","series_processed":len(completed),"results":completed}
