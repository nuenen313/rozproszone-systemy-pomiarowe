import json

import paho.mqtt.client as mqtt
import psycopg2

MQTT_HOST="broker"
MQTT_PORT=1883
MQTT_TOPIC="lab/+/+/+"
DB_HOST="postgres"
DB_NAME="abcd_db"
DB_USER="admin"
DB_PASSWORD="admin_pass1234"

def save_measurement(data):
    conn = psycopg2.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD)
    cur = conn.cursor()
    cur.execute("""
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
            data["seq"]
        )
    )
    conn.commit()
    cur.close()
    conn.close()



def is_valid(data):
    required = ["schema_version", "device_id", "sensor", "sensor_value", "unit", "ts_ms", "seq"]
    return all(field in data for field in required)


def on_connect(client, userdata, flags, rc):
    print("Connected with result code", rc)
    client.subscribe(MQTT_TOPIC)


def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode("utf-8")
        data = json.loads(payload)
        if not is_valid(data):
            print("Invalid payload:", data)
            return
        save_measurement(data)
        print("Saved message from topic:", msg.topic)
    except Exception as e:
        print("Error:", e)


client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect(MQTT_HOST, MQTT_PORT, 60)
client.loop_forever()