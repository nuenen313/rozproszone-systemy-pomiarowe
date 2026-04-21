from flask import Flask, jsonify, request
from db import get_connection

app = Flask(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def measurement_to_dict(row):
    return {
        "id":             row[0],
        "schema_version": row[1],
        "device_id":      row[2],
        "sensor":         row[3],
        "sensor_value":   row[4],
        "unit":           row[5],
        "ts_ms":          row[6],
        "seq":            row[7],
    }


def status_to_dict(row):
    return {
        "device_id":  row[0],
        "group_id":   row[1],
        "is_online":  row[2],
        "updated_at": row[3],
    }


# ---------------------------------------------------------------------------
# General
# ---------------------------------------------------------------------------

@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


# ---------------------------------------------------------------------------
# Device status  (device_status table)
# ---------------------------------------------------------------------------

@app.route("/devices")
def get_devices():
    """All known devices with their current online status."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT device_id, group_id, is_online, updated_at
        FROM device_status
        ORDER BY group_id, device_id
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify([status_to_dict(row) for row in rows])


@app.route("/devices/<device_id>")
def get_device(device_id):
    """Online status for a single device."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT device_id, group_id, is_online, updated_at
        FROM device_status
        WHERE device_id = %s
    """, (device_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row is None:
        return jsonify({"message": "Device not found"}), 404
    return jsonify(status_to_dict(row))


# ---------------------------------------------------------------------------
# Measurements  (measurements table)
# ---------------------------------------------------------------------------

@app.route("/measurements")
def get_measurements():
    """Most recent 20 measurements across all devices."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, schema_version, device_id, sensor, sensor_value, unit, ts_ms, seq
        FROM measurements
        ORDER BY id DESC
        LIMIT 20
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify([measurement_to_dict(row) for row in rows])


@app.route("/measurements/latest")
def get_latest_measurement():
    """Single most recent measurement."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, schema_version, device_id, sensor, sensor_value, unit, ts_ms, seq
        FROM measurements
        ORDER BY id DESC
        LIMIT 1
    """)
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row is None:
        return jsonify({"message": "Brak danych"}), 404
    return jsonify(measurement_to_dict(row))


@app.route("/measurements/history")
def get_measurement_history():
    """
    Filtered measurement history.
    Query params:
      device_id  (optional)
      sensor     (optional)
      limit      (optional, default 20)
    """
    device_id = request.args.get("device_id")
    sensor    = request.args.get("sensor")
    limit     = request.args.get("limit", default=20, type=int)

    conn = get_connection()
    cur = conn.cursor()
    query = """
        SELECT id, schema_version, device_id, sensor, sensor_value, unit, ts_ms, seq
        FROM measurements
        WHERE 1=1
    """
    params = []
    if device_id:
        query += " AND device_id = %s"
        params.append(device_id)
    if sensor:
        query += " AND sensor = %s"
        params.append(sensor)
    query += " ORDER BY id DESC LIMIT %s"
    params.append(limit)

    cur.execute(query, params)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify([measurement_to_dict(row) for row in rows])


# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)