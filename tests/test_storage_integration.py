"""Pruebas con PostgreSQL real: RUN_DB_TESTS=1 python -m pytest -q."""
import json
import os
import uuid
import pytest
from psycopg import sql
from src.config import ROOT
from src.storage import connect, load_model, process_message
from tests.test_contract import valid_event

pytestmark=pytest.mark.skipif(os.getenv('RUN_DB_TESTS')!='1',reason='Requiere PostgreSQL local y RUN_DB_TESTS=1')

@pytest.fixture
def database():
    conn=connect()
    conn.autocommit=True
    schema='test_'+uuid.uuid4().hex
    conn.execute(sql.SQL('CREATE SCHEMA {}').format(sql.Identifier(schema)))
    conn.execute(sql.SQL('SET search_path TO {}').format(sql.Identifier(schema)))
    conn.execute((ROOT/'sql/create_tables.sql').read_text(encoding='utf-8'))
    yield conn
    conn.execute('SET search_path TO public')
    conn.execute(sql.SQL('DROP SCHEMA {} CASCADE').format(sql.Identifier(schema)))
    conn.close()

def test_exact_raw_and_replay(database):
    model,meta=load_model()
    payload=('  '+json.dumps(valid_event(),indent=2)+'\n').encode()
    args=(database,model,meta,'test',0,0,b'Colombia',payload)
    assert process_message(*args)=='VALID'
    assert process_message(*args)=='VALID'
    assert database.execute('SELECT count(*) FROM fact_predictions').fetchone()[0]==1
    assert bytes(database.execute('SELECT payload FROM raw_happiness_events').fetchone()[0])==payload
    assert process_message(database,model,meta,'test',0,1,b'Colombia',payload)=='DUPLICATE'
    assert database.execute('SELECT count(*) FROM fact_predictions').fetchone()[0]==1

def test_invalid_then_valid(database):
    model,meta=load_model()
    assert process_message(database,model,meta,'test',0,0,b'Colombia',b'not json')=='INVALID_SCHEMA'
    assert process_message(database,model,meta,'test',0,1,b'Colombia',json.dumps(valid_event()).encode())=='VALID'
    assert database.execute('SELECT count(*) FROM raw_happiness_events').fetchone()[0]==2
    assert database.execute('SELECT count(*) FROM fact_predictions').fetchone()[0]==1

def test_prediction_failure_keeps_original(database):
    class BrokenModel:
        def predict(self, features):
            raise RuntimeError('Simulated model failure')
    _,meta=load_model()
    payload=json.dumps(valid_event()).encode()
    assert process_message(database,BrokenModel(),meta,'test',0,0,b'Colombia',payload)=='PREDICTION_ERROR'
    assert database.execute('SELECT count(*) FROM fact_predictions').fetchone()[0]==0
    assert bytes(database.execute('SELECT payload FROM raw_happiness_events').fetchone()[0])==payload
