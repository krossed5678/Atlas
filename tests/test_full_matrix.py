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

def test_reviewed_email_and_dropship_drafts_are_gated():
    lead=client.post('/api/leads',json={'email':'draft@example.com'}).json()
    draft=client.post('/api/outreach/drafts',json={'lead_id':lead['id'],'subject':'A relevant video idea','body':'I created a concise promotional-video concept for your property.'})
    assert draft.status_code == 200
    assert client.post(f"/api/outreach/drafts/{draft.json()['id']}/approve").json()['sent'] is False
    client.post(f"/api/leads/{lead['id']}/opt-out")
    assert client.post('/api/outreach/drafts',json={'lead_id':lead['id'],'subject':'No contact','body':'This must be rejected because the lead opted out.'}).status_code == 403
    product=client.post('/api/commerce/tiktok/products',json={'title':'Travel Pillow','supplier_name':'Example Supplier','supplier_sku':'TP-1','cost_cents':900,'sale_cents':1900})
    assert product.status_code == 200 and product.json()['status'] == 'DRAFT'
    order=client.post('/api/commerce/orders',json={'product_id':product.json()['id'],'external_order_id':'order-1','quantity':1})
    assert order.json()['status'] == 'PENDING_FULFILLMENT'
    assert client.post('/api/commerce/orders',json={'product_id':product.json()['id'],'external_order_id':'order-1','quantity':1}).status_code == 409
