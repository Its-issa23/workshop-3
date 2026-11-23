import json
import math
from datetime import datetime
from .config import FEATURES

class InvalidEvent(ValueError):
    def __init__(self, status, reason):
        super().__init__(reason)
        self.status = status

def validate(payload, key):
    try:
        event = json.loads(payload)
    except (ValueError, UnicodeDecodeError):
        raise InvalidEvent('INVALID_SCHEMA', 'JSON inválido')
    fields = ['event_id', 'country', 'year', *FEATURES, 'actual_happiness_score', 'event_time']
    if not isinstance(event, dict) or any(f not in event for f in fields):
        raise InvalidEvent('INVALID_SCHEMA', 'Faltan campos obligatorios o no es un objeto')
    for col in ['event_id', 'country', 'event_time']:
        if not isinstance(event[col], str) or not event[col].strip():
            raise InvalidEvent('INVALID_SCHEMA', f'{col}: se requiere texto no vacío')
    if type(event['year']) is not int:
        raise InvalidEvent('INVALID_SCHEMA', 'year debe ser entero')
    if not 2015 <= event['year'] <= 2019:
        raise InvalidEvent('INVALID_VALUES', 'year fuera de la fuente histórica 2015–2019')
    for col in [*FEATURES, 'actual_happiness_score']:
        value = event[col]
        if type(value) not in (int, float):
            raise InvalidEvent('INVALID_SCHEMA', f'{col}: se requiere un número')
        if not math.isfinite(value) or value < 0:
            raise InvalidEvent('INVALID_VALUES', f'{col}: valor no finito o negativo')
    if not 0 <= event['actual_happiness_score'] <= 10:
        raise InvalidEvent('INVALID_VALUES', 'Puntaje fuera de 0–10')
    try:
        timestamp = datetime.fromisoformat(event['event_time'].replace('Z', '+00:00'))
        if 'T' not in event['event_time'] or timestamp.tzinfo is None:
            raise ValueError()
    except ValueError:
        raise InvalidEvent('INVALID_VALUES', 'event_time requiere ISO-8601 con zona horaria')
    if key != event['country'].encode('utf-8'):
        raise InvalidEvent('INVALID_VALUES', 'La clave Kafka no coincide con country')
    return event
