CREATE TABLE IF NOT EXISTS sensor (
    uuid       UUID PRIMARY KEY,
    name       TEXT NOT NULL,
    type       TEXT,
    sensor     TEXT,
    apidetails TEXT,
    is_online  BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS measurements (
    id             SERIAL  PRIMARY KEY,
    schema_version TEXT    NOT NULL,
    device_id      TEXT    NOT NULL,
    sensor         TEXT    NOT NULL,
    sensor_value   REAL    NOT NULL,
    unit           TEXT    NOT NULL,
    ts_ms          BIGINT  NOT NULL,
    seq            INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS device_status (
    device_id  TEXT    PRIMARY KEY,
    group_id   TEXT    NOT NULL,
    is_online  BOOLEAN NOT NULL DEFAULT FALSE,
    updated_at BIGINT  NOT NULL
);

-- Seed mock data on startup
INSERT INTO sensor (uuid, name, type, sensor, apidetails, is_online)
VALUES
    ('11111111-1111-1111-1111-111111111111', 'Temperature Sensor A', 'temperature', 'TMP36', '{"unit":"C"}', TRUE),
    ('22222222-2222-2222-2222-222222222222', 'Humidity Sensor B', 'humidity', 'DHT22', '{"unit":"%"}', TRUE),
    ('33333333-3333-3333-3333-333333333333', 'Azimuth Sensor C', 'azimuth', 'HMC5883L', '{"unit":"deg"}', FALSE)
ON CONFLICT (uuid) DO NOTHING;

INSERT INTO measurements (schema_version, device_id, sensor, sensor_value, unit, ts_ms, seq)
VALUES
    ('1.0', 'esp32-abcd01', 'temperature', 21.5, 'C', 1742030400000, 15),
    ('1.0', 'esp32-abcd02', 'humidity', 55, '%', 1742030440000, 16),
    ('1.0', 'esp32-abcd03', 'azimuth', 180.0, 'deg', 1742030460000, 17);

INSERT INTO device_status (device_id, group_id, is_online, updated_at)
VALUES
    ('esp32-abcd01', 'g05', TRUE, 1682505600000),
    ('esp32-abcd02', 'g05', TRUE, 1682505660000),
    ('esp32-abcd03', 'g05', FALSE, 1682505720000)
ON CONFLICT (device_id) DO NOTHING;