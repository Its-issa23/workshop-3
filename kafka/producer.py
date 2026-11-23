import argparse
import json
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pandas as pd
from confluent_kafka import Producer
from confluent_kafka.admin import AdminClient, NewTopic
from confluent_kafka import KafkaException, KafkaError
from src.config import BOOTSTRAP, TOPIC, FEATURES
from src.data import load_data

def ensure_topic():
    admin = AdminClient({'bootstrap.servers': BOOTSTRAP, 'broker.address.family':'v4'})
    for future in admin.create_topics([NewTopic(TOPIC, num_partitions=3, replication_factor=1)]).values():
        try:
            future.result()
        except KafkaException as exc:
            if exc.args[0].code() != KafkaError.TOPIC_ALREADY_EXISTS:
                raise
    topic = admin.list_topics(TOPIC, timeout=20).topics[TOPIC]
    if len(topic.partitions) != 3 or any(len(p.replicas) != 1 for p in topic.partitions.values()):
        raise RuntimeError('El topic debe tener 3 particiones y factor de replicación 1')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--delay', type=float, default=0.1)
    parser.add_argument('--limit', type=int)
    parser.add_argument('--demo-invalid', action='store_true')
    args = parser.parse_args()
    if args.delay < 0:
        parser.error('--delay debe ser >= 0')
    ensure_topic()
    producer = Producer({'bootstrap.servers':BOOTSTRAP, 'broker.address.family':'v4', 'enable.idempotence':True, 'acks':'all'})
    failures = []
    def delivered(err, msg):
        if err:
            failures.append(str(err))
    run = str(uuid.uuid4())
    data = load_data()
    if args.limit is not None:
        data = data.head(args.limit)
    count = 0
    for row in data.to_dict('records'):
        event = dict(event_id=f'{run}:{count}',country=row['country'],year=int(row['year']),
                     **{f:None if pd.isna(row[f]) else float(row[f]) for f in FEATURES},
                     actual_happiness_score=float(row['happiness_score']),event_time=datetime.now(timezone.utc).isoformat())
        producer.produce(TOPIC,key=event['country'].encode(),value=json.dumps(event,allow_nan=False).encode(),on_delivery=delivered)
        producer.poll(0)
        count += 1
        time.sleep(args.delay)
    if args.demo_invalid:
        for payload in [b'{broken json', b'{"country":"Colombia"}']:
            producer.produce(TOPIC,key=b'Colombia',value=payload,on_delivery=delivered)
            count += 1
    remaining = producer.flush(30)
    if remaining or failures:
        raise RuntimeError(f'Entrega incompleta: pendientes={remaining}, errores={failures}')
    print(f'Eventos confirmados por Kafka: {count}. run_id={run}')

if __name__ == '__main__':
    main()
