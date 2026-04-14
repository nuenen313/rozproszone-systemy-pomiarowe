CREATE TABLE IF NOT EXISTS sensor (
    uuid UUID PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT,
    sensor TEXT,
    apidetails TEXT,
    is_online BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS measurements (
    id SERIAL PRIMARY KEY,
    schema_version TEXT NOT NULL,
    device_id TEXT NOT NULL,
    sensor TEXT NOT NULL,
    sensor_value REAL NOT NULL,
    unit TEXT NOT NULL,
    ts_ms BIGINT NOT NULL,
    seq INTEGER NOT NULL
);