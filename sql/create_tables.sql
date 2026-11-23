CREATE TABLE IF NOT EXISTS raw_happiness_events (
    raw_event_id BIGSERIAL PRIMARY KEY,
    topic TEXT NOT NULL,
    partition_id INTEGER NOT NULL,
    offset_id BIGINT NOT NULL,
    kafka_key BYTEA,
    payload BYTEA,
    received_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    event_id TEXT,
    event_time TIMESTAMPTZ,
    processing_status TEXT NOT NULL DEFAULT 'RECEIVED'
      CHECK (processing_status IN ('RECEIVED','VALID','INVALID_SCHEMA','INVALID_VALUES','PREDICTION_ERROR','DUPLICATE')),
    error_message TEXT,
    UNIQUE(topic, partition_id, offset_id)
);
CREATE TABLE IF NOT EXISTS dim_country (
    country_id BIGSERIAL PRIMARY KEY,
    country_name TEXT NOT NULL UNIQUE
);
-- Fecha de emisión, distinta del año histórico de la observación.
CREATE TABLE IF NOT EXISTS dim_date (
    date_id INTEGER PRIMARY KEY,
    full_date DATE NOT NULL UNIQUE,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    day INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS fact_predictions (
    prediction_id BIGSERIAL PRIMARY KEY,
    raw_event_id BIGINT NOT NULL UNIQUE REFERENCES raw_happiness_events(raw_event_id),
    event_id TEXT NOT NULL UNIQUE,
    country_id BIGINT NOT NULL REFERENCES dim_country(country_id),
    date_id INTEGER NOT NULL REFERENCES dim_date(date_id),
    observation_year INTEGER NOT NULL,
    actual_score DOUBLE PRECISION NOT NULL,
    predicted_score DOUBLE PRECISION NOT NULL,
    prediction_error DOUBLE PRECISION NOT NULL,
    absolute_error DOUBLE PRECISION NOT NULL,
    event_time TIMESTAMPTZ NOT NULL,
    prediction_timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    model_version TEXT NOT NULL,
    evaluation_split TEXT NOT NULL
);
CREATE OR REPLACE VIEW vw_predictions AS
SELECT f.*, c.country_name, d.full_date,
       EXTRACT(EPOCH FROM (f.prediction_timestamp-f.event_time))*1000 AS latency_ms
FROM fact_predictions f
JOIN dim_country c USING(country_id)
JOIN dim_date d USING(date_id);
CREATE OR REPLACE VIEW vw_processing_status AS
SELECT processing_status, COUNT(*) AS event_count FROM raw_happiness_events GROUP BY processing_status;
