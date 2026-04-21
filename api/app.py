from flask import Flask, jsonify, request
from db import get_connection

app = Flask(__name__)


@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


def row_to_dict(row):
    return {
        "id": row[0],
        "schema_version": row[1],
        "device_id": row[2],
        "sensor": row[3],
        "sensor_value": row[4],
        "unit": row[5],
        "ts_ms": row[6],
        "seq": row[7],
    }


@app.route("/measurements")
def get_measurements():
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
    return jsonify([row_to_dict(row) for row in rows])


@app.route("/measurements/latest")
def get_latest_measurement():
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
    return jsonify(row_to_dict(row))


@app.route("/measurements/history")
def get_measurement_history():
    device_id = request.args.get("device_id")
    sensor = request.args.get("sensor")
    limit = request.args.get("limit", default=20, type=int)

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
    return jsonify([row_to_dict(row) for row in rows])


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)