from fastapi.testclient import TestClient
from app.main import app
client=TestClient(app)
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

def test_folder_photo_set_import(tmp_path):
    sample=tmp_path/'photos'; sample.mkdir(); (sample/'room.jpg').write_bytes(b'not-a-real-image-but-valid-intake-file')
    result=client.post('/api/properties/import-folder',json={'folder_path':str(sample)})
    assert result.status_code==200 and result.json()['image_count']==1

def test_default_commerce_selection_is_safe():
    system = client.get('/api/system').json()
    assert system['commerce']['shopify_store'] == 'x6qufc-nh.myshopify.com'
    assert system['commerce']['stripe_context'] == 'acct_1SPAFpI0vp8qwDso'
    assert system['commerce']['stripe_livemode'] is False
    assert system['commerce']['creator_payouts'] == 'human_approval_required'
    tiktok = client.get('/api/commerce/tiktok/readiness').json()
    assert tiktok['ready'] is False and tiktok['writes_enabled'] is False
