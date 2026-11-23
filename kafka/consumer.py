import argparse
import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from confluent_kafka import Consumer, KafkaException
from src.config import BOOTSTRAP, TOPIC, GROUP
from src.storage import connect, initialize, load_model, process_message

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--idle-timeout', type=float, default=0, help='0 mantiene el consumidor activo')
    args = parser.parse_args()
    initialize()
    model, metadata = load_model()
    consumer = Consumer({'bootstrap.servers':BOOTSTRAP,'broker.address.family':'v4','group.id':GROUP,
                         'auto.offset.reset':'earliest','enable.auto.commit':False})
    conn = connect()
    consumer.subscribe([TOPIC])
    last_message = time.monotonic()
    try:
        while True:
            msg = consumer.poll(1)
            if msg is None:
                if args.idle_timeout and time.monotonic()-last_message >= args.idle_timeout:
                    break
                continue
            if msg.error():
                raise KafkaException(msg.error())
            last_message = time.monotonic()
            status = process_message(conn,model,metadata,msg.topic(),msg.partition(),msg.offset(),msg.key(),msg.value())
            # Solo confirmar en Kafka cuando la escritura SQL es durable.
            consumer.commit(message=msg,asynchronous=False)
            print(f'{msg.partition()}:{msg.offset()} {status}',flush=True)
    except KeyboardInterrupt:
        print('Consumidor detenido')
    finally:
        conn.close()
        consumer.close()

if __name__ == '__main__':
    main()
