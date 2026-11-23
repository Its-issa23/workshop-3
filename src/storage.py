import json
import pickle
from datetime import datetime, timezone
import pandas as pd
import psycopg
from .config import ROOT, FEATURES, db_config
from .contract import validate, InvalidEvent

def connect():
    return psycopg.connect(**db_config())

def initialize():
    with connect() as conn:
        conn.execute((ROOT / 'sql/create_tables.sql').read_text(encoding='utf-8'))

def load_model():
    model = pickle.loads((ROOT / 'models/model.pkl').read_bytes())
    metadata = json.loads((ROOT / 'models/metadata.json').read_text())
    if list(model.feature_names_in_) != FEATURES or metadata['features'] != FEATURES:
        raise ValueError('Esquema del modelo incompatible')
    return model, metadata

def process_message(conn, model, metadata, topic, partition, offset, key, payload):
    # Commit separado: incluso si luego hay un fallo, se conserva el original.
    with conn.transaction():
        row = conn.execute('''INSERT INTO raw_happiness_events(topic,partition_id,offset_id,kafka_key,payload)
            VALUES (%s,%s,%s,%s,%s) ON CONFLICT(topic,partition_id,offset_id)
            DO UPDATE SET topic=EXCLUDED.topic RETURNING raw_event_id, processing_status''',
            (topic, partition, offset, key, payload)).fetchone()
    raw_id, status = row
    if status != 'RECEIVED':
        return status
    try:
        event = validate(payload, key)
    except (InvalidEvent, TypeError) as exc:
        status = getattr(exc, 'status', 'INVALID_SCHEMA')
        with conn.transaction():
            conn.execute('UPDATE raw_happiness_events SET processing_status=%s,error_message=%s WHERE raw_event_id=%s', (status,str(exc),raw_id))
        return status
    try:
        predicted = float(model.predict(pd.DataFrame([{f:event[f] for f in FEATURES}], columns=FEATURES))[0])
        import math
        if not math.isfinite(predicted):
            raise ValueError('Predicción no finita')
    except Exception as exc:
        with conn.transaction():
            conn.execute("UPDATE raw_happiness_events SET processing_status='PREDICTION_ERROR',error_message=%s WHERE raw_event_id=%s", (str(exc),raw_id))
        return 'PREDICTION_ERROR'
    timestamp = datetime.fromisoformat(event['event_time'].replace('Z','+00:00')).astimezone(timezone.utc)
    date = timestamp.date()
    date_id = int(date.strftime('%Y%m%d'))
    error = predicted - event['actual_happiness_score']
    with conn.transaction():
        country_id = conn.execute('''INSERT INTO dim_country(country_name) VALUES (%s)
            ON CONFLICT(country_name) DO UPDATE SET country_name=EXCLUDED.country_name RETURNING country_id''', (event['country'],)).fetchone()[0]
        conn.execute('INSERT INTO dim_date VALUES (%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING', (date_id,date,date.year,date.month,date.day))
        inserted = conn.execute('''INSERT INTO fact_predictions
            (raw_event_id,event_id,country_id,date_id,observation_year,actual_score,predicted_score,prediction_error,absolute_error,event_time,model_version,evaluation_split)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT(event_id) DO NOTHING RETURNING prediction_id''',
            (raw_id,event['event_id'],country_id,date_id,event['year'],event['actual_happiness_score'],predicted,error,abs(error),timestamp,
             metadata['model_sha256'], 'test' if event['year'] in metadata['test_years'] else 'train')).fetchone()
        status = 'VALID' if inserted else 'DUPLICATE'
        conn.execute('''UPDATE raw_happiness_events SET processing_status=%s,event_id=%s,event_time=%s WHERE raw_event_id=%s''',
                     (status,event['event_id'],timestamp,raw_id))
    return status

if __name__ == '__main__':
    initialize()
