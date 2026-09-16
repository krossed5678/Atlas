import os, shutil, uuid
os.environ['ASTRA_DATA_DIR']='/tmp/astra-test'
from fastapi.testclient import TestClient
from app.main import app, init_db
client=TestClient(app)
def setup_function(): shutil.rmtree('/tmp/astra-test',ignore_errors=True);init_db()
def test_duplicate_ledger_and_refund_reduces_capital():
    assert client.post('/api/ledger',json={'kind':'revenue','amount_cents':40000,'reference_id':'r'}).status_code==200
    assert client.post('/api/ledger',json={'kind':'revenue','amount_cents':40000,'reference_id':'r'}).status_code==409
    client.post('/api/ledger',json={'kind':'refund','amount_cents':20000,'reference_id':'f'})
    assert client.get('/api/ledger/capital').json()['available_trading_capital_cents']==5000
def test_duplicate_lead_and_optout():
    first=client.post('/api/leads',json={'email':'host@example.com'}); assert first.status_code==200
    assert client.post('/api/leads',json={'email':'host@example.com'}).status_code==409
    assert client.post(f"/api/leads/{first.json()['id']}/opt-out").status_code==200
def test_duplicate_trade_and_live_gate():
    client.post('/api/ledger',json={'kind':'revenue','amount_cents':100000,'reference_id':'fund'})
    x={'symbol':'BTC-USD','side':'buy','quantity':1,'price':10,'idempotency_key':'once'}
    assert client.post('/api/trades',json=x).status_code==200
    assert client.post('/api/trades',json=x).status_code==409
    x['idempotency_key']='live';x['mode']='LIVE_READY_HANDOFF';assert client.post('/api/trades',json=x).status_code==403
