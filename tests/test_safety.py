import os
import shutil
import pytest
os.environ['ASTRA_DATA_DIR'] = '/tmp/astra-test'
from fastapi.testclient import TestClient
from app.main import app, init_db

client=TestClient(app)
@pytest.fixture(autouse=True)
def isolated_database():
    shutil.rmtree('/tmp/astra-test', ignore_errors=True)
    init_db()
    yield
    shutil.rmtree('/tmp/astra-test', ignore_errors=True)
def test_capital_boundary_and_stop():
    client.post('/api/ledger',json={'kind':'revenue','amount_cents':10000,'reference_id':'sale-1'})
    assert client.get('/api/ledger/capital').json()['available_trading_capital_cents']==2500
    bad=client.post('/api/trades',json={'symbol':'BTC-USD','side':'buy','quantity':1,'price':30,'idempotency_key':'x'})
    assert bad.status_code==400
    client.post('/api/system/emergency-stop')
    stopped=client.post('/api/trades',json={'symbol':'BTC-USD','side':'buy','quantity':1,'price':10,'idempotency_key':'y'})
    assert stopped.status_code==423
def test_contract_validation():
    c=client.post('/api/creators',json={'name':'A','email':'a@example.com'}).json()
    r=client.post('/api/contracts',json={'creator_id':c['id'],'terms':{}})
    assert r.status_code==400
