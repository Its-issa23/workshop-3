import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / '.env')
FEATURES = ['gdp', 'family', 'health', 'freedom', 'generosity', 'corruption']
TOPIC = 'happiness-events'
GROUP = 'happiness-ml-team'
BOOTSTRAP = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:29092')

def db_config():
    return dict(host=os.getenv('DB_HOST', '127.0.0.1'), port=int(os.getenv('DB_PORT', '5433')), connect_timeout=10,
                dbname=os.getenv('DB_NAME', 'happiness'), user=os.getenv('DB_USER', 'happiness'),
                password=os.getenv('DB_PASSWORD', 'local_workshop_only'))
