import json
import time

import paho.mqtt.client as mqtt
import psycopg2

MQTT_HOST = "broker"
MQTT_PORT = 1883
MQTT_TOPIC = "lab/+/+/+"

DB_HOST = "database"
DB_NAME = "abcd_db"
DB_USER = "admin"
DB_PASSWORD = "admin_pass1234"


def get_conn():
    return psycopg2.connect(
        host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD
    )


def save_measurement(data):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO measurements
            (schema_version, device_id, sensor, sensor_value, unit, ts_ms, seq)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        (
            data["schema_version"],
            data["device_id"],
            data["sensor"],
            data["sensor_value"],
            data["unit"],
            data["ts_ms"],
            data["seq"],
        ),
    )
    conn.commit()
    cur.close()
    conn.close()


def upsert_device_status(device_id: str, group_id: str, is_online: bool):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO device_status (device_id, group_id, is_online, updated_at)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (device_id) DO UPDATE
            SET is_online  = EXCLUDED.is_online,
                updated_at = EXCLUDED.updated_at
        """,
        (device_id, group_id, is_online, int(time.time() * 1000)),
    )
    conn.commit()
    cur.close()
    conn.close()


def is_valid(data):
    required = ["schema_version", "device_id", "sensor", "sensor_value", "unit", "ts_ms", "seq"]
    return all(field in data for field in required)


def parse_topic(topic: str):
    """
    Expected format: lab/{group_id}/{device_id}/{leaf}
    Returns (group_id, device_id, leaf) or None if malformed.
    """
    parts = topic.split("/")
    if len(parts) != 4 or parts[0] != "lab":
        return None
    return parts[1], parts[2], parts[3]


def on_connect(client, userdata, flags, rc):
    print("Connected with result code", rc)
    client.subscribe(MQTT_TOPIC)


def on_message(client, userdata, msg):
    try:
        parsed = parse_topic(msg.topic)
        if parsed is None:
            print("Unexpected topic format:", msg.topic)
            return

        group_id, device_id, leaf = parsed

        if leaf == "status":
            status = msg.payload.decode("utf-8").strip()
            is_online = status == "online"
            upsert_device_status(device_id, group_id, is_online)
            print(f"Status update: {device_id} -> {status}")
            return

        data = json.loads(msg.payload.decode("utf-8"))
        if not is_valid(data):
            print("Invalid payload:", data)
            return

        save_measurement(data)
        print("Saved measurement from topic:", msg.topic)

    except Exception as e:
        print("Error:", e)


client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect(MQTT_HOST, MQTT_PORT, 60)
client.loop_forever()