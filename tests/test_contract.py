import json
import pytest
from src.contract import validate, InvalidEvent

def valid_event():
    return dict(event_id='E001',country='Colombia',year=2019,gdp=1.2,family=0.8,health=0.9,
                freedom=0.6,generosity=0.3,corruption=0.1,actual_happiness_score=6.2,
                event_time='2026-11-22T12:00:00+00:00')

def test_valid():
    assert validate(json.dumps(valid_event()).encode(),b'Colombia')['year']==2019

@pytest.mark.parametrize('field,value,status', [('gdp',None,'INVALID_SCHEMA'),('year',True,'INVALID_SCHEMA'),
    ('health',float('nan'),'INVALID_VALUES'),('freedom',-1,'INVALID_VALUES'),
    ('actual_happiness_score',11,'INVALID_VALUES'),('event_time','2026-11-22','INVALID_VALUES'),
    ('country',' ','INVALID_SCHEMA'),('year',2020,'INVALID_VALUES')])
def test_invalid(field,value,status):
    event=valid_event(); event[field]=value
    with pytest.raises(InvalidEvent) as exc:
        validate(json.dumps(event).encode(),b'Colombia')
    assert exc.value.status==status

@pytest.mark.parametrize('payload', [b'{',b'[]',b'{}',b'\xff'])
def test_invalid_payload(payload):
    with pytest.raises(InvalidEvent):
        validate(payload,b'Colombia')

def test_wrong_key():
    with pytest.raises(InvalidEvent):
        validate(json.dumps(valid_event()).encode(),b'Peru')
