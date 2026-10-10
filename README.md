# Distributed Measurement System

A small end-to-end IoT measurement pipeline: **ESP32** devices publish sensor readings over **MQTT**, an **ingestor** service stores them in **PostgreSQL**, a **Flask REST API** exposes the data, and a **PyQt6 desktop dashboard** displays it.

<img width="1110" height="788" alt="preview" src="https://github.com/user-attachments/assets/97172d76-90bd-43d7-b2dd-87dfabb77d83" />


---

## Architecture

```text
┌──────────┐   MQTT (1883)   ┌──────────┐   subscribe lab/+/+/+   ┌──────────┐   INSERT / UPSERT   ┌────────────┐
│  ESP32   │ ──────────────▶ │  broker  │ ──────────────────────▶ │ ingestor │ ──────────────────▶ │ PostgreSQL │
│ firmware │                 │Mosquitto │                         │ (Python) │                     │  (5432)    │
└──────────┘                 └──────────┘                         └──────────┘                     └─────┬──────┘
                                                                                                         │ SELECT
                                                    ┌─────────────────┐   HTTP (5001)   ┌──────────┐     │
                                                    │  UI dashboard   │ ◀────────────── │ Flask API│ ◀───┘
                                                    │    (PyQt6)      │                 └──────────┘
                                                    └─────────────────┘
```

| Component | Location | Technology | Role |
|---|---|---|---|
| Firmware | `esp32/` | PlatformIO, Arduino, PubSubClient, ArduinoJson | Publishes measurements and status every 5 s |
| Broker | `broker/` | Eclipse Mosquitto | MQTT message broker |
| Ingestor | `ingestor/` | Python, paho-mqtt, psycopg2 | Subscribes to `lab/+/+/+`, validates and stores messages |
| Database | `database/` | PostgreSQL 18 | Stores measurements and device status |
| API | `api/` | Flask, psycopg2, SQLAlchemy | Read-only REST access to the data |
| UI | `ui/` | PyQt6, matplotlib, requests | Desktop dashboard (latest value, history chart, auto-refresh) |
| Docs | `docs/` | Markdown | MQTT message contract (`message_contract.md`, in Polish) |

---

## Requirements

- Docker + Docker Compose
- Python 3.10+ (for the UI)
- [PlatformIO](https://platformio.org/) (to build and flash the ESP32 firmware)
- An ESP32 dev board (`esp32dev`)
- Optional: [MQTT Explorer](https://mqtt-explorer.com/) or `mosquitto-clients` for inspecting the broker

---

## Quick start

### 1. Clone the repository

```bash
git clone https://github.com/nuenen313/rozproszone-systemy-pomiarowe.git
cd rozproszone-systemy-pomiarowe
```

### 2. Start the backend

```bash
docker compose up -d --build
```

This builds and starts four services:

| Compose service | Container name | Port |
|---|---|---|
| `flask` | `api` | 5001 |
| `broker` | `broker` | 1883 |
| `database` | `postgres` | 5432 |
| `ingestor` | `ingestor` | — |

### 3. Check status and logs

```bash
docker compose ps
docker compose logs -f              # all services
docker compose logs -f ingestor     # a single service (use the service name, e.g. flask, broker, database, ingestor)
```

When a device is publishing, the ingestor log should show one status update and four saved measurements every ~5 s:

<img width="1166" height="619" alt="preview2" src="https://github.com/user-attachments/assets/86c3915d-24cf-4a7c-bf99-6e40568bde97" />


### 4. Stop the backend

```bash
docker compose down
```

> **Note:** the database has no named volume, so stored measurements are not kept after `docker compose down`. On every fresh start the database is re-initialised with a few mock rows (`esp32-abcd01` … `esp32-abcd03`).

---

## ESP32 firmware

### Configuration

Wi-Fi and MQTT settings are read from `esp32/include/secrets.h`. This file is **git-ignored**, so you must create it yourself:

```cpp
// esp32/include/secrets.h
#pragma once

#define WIFI_SSID     "your-wifi-ssid"
#define WIFI_PASSWORD "your-wifi-password"

#define MQTT_HOST     "192.168.1.100"   // LAN IP of the machine running Docker (not "localhost")
#define MQTT_PORT     1883
#define MQTT_GROUP    "g05"             // group id used in the topic
```

### Build, flash and monitor

```bash
cd esp32
pio run -t upload        # upload_port is set to /dev/ttyUSB0 in platformio.ini
pio device monitor       # 115200 baud
```

### What the firmware does

- Generates a device ID from the chip eFuse MAC (e.g. `esp32-1C0B58FE8CE0`) and stores it in flash (NVS) so it stays the same across reboots.
- Synchronises time via NTP (`pool.ntp.org`, `time.nist.gov`) so `ts_ms` is a real Unix timestamp.
- Every **5 seconds** publishes:
  - `online` to `lab/{MQTT_GROUP}/{deviceId}/status`
  - one JSON message per sensor:

| Sensor | Unit | Source |
|---|---|---|
| `temperature` | `C` | simulated (sine, 20 ± 10, period 60 s) |
| `humidity` | `%` | simulated (sine, 50 ± 20, period 45 s) |
| `azimuth` | `deg` | simulated (sine, 180 ± 180, period 30 s) |
| `core_temperature` | `C` | real ESP32 internal temperature sensor |

- Each sensor has its own `seq` counter, incremented on every publish.

---

## MQTT

### Topics

```text
lab/{group_id}/{device_id}/{sensor}     # measurements (JSON)
lab/{group_id}/{device_id}/status       # device status (plain text, e.g. "online")
```

Example: `lab/g05/esp32-1C0B58FE8CE0/temperature`

### Message format (schema v1.0)

```json
{
  "schema_version": "1.0",
  "device_id": "esp32-1C0B58FE8CE0",
  "sensor": "temperature",
  "sensor_value": 25.5,
  "unit": "C",
  "ts_ms": 1760107685000,
  "seq": 43
}
```

All fields are required; messages missing any of them are rejected by the ingestor. The full contract (validation rules, invalid-message examples) is in [docs/message_contract.md](docs/message_contract.md).

### Connecting to the broker

The broker accepts anonymous connections ([broker/mosquitto.conf](broker/mosquitto.conf)):

```conf
allow_anonymous true
listener 1883
```

- Host: `localhost` (from the host machine) or `broker` (from inside the Docker network)
- Port: `1883`
- Username / password: empty

```bash
mosquitto_sub -h localhost -p 1883 -t 'lab/#' -v
```
<img width="1022" height="758" alt="preview3" src="https://github.com/user-attachments/assets/fdcc80ea-0e41-4a68-9214-bc61c5d81fdd" />

> This configuration is intended for a lab environment and is not production-safe.

---

## Database

Connection parameters (from the host machine):

| Parameter | Value |
|---|---|
| Host | `localhost` |
| Port | `5432` |
| User | `admin` |
| Password | `admin_pass1234` |
| Database | `abcd_db` |

Tables (created by [database/01-init_database.sql](database/01-init_database.sql)):

| Table | Contents |
|---|---|
| `measurements` | One row per received measurement (`schema_version`, `device_id`, `sensor`, `sensor_value`, `unit`, `ts_ms`, `seq`) |
| `device_status` | Latest status per device (`device_id`, `group_id`, `is_online`, `updated_at`) — upserted by the ingestor |
| `sensor` | Static sensor catalogue (mock data, not used by the API) |

Quick check:

```bash
docker exec -it postgres psql -U admin -d abcd_db -c "SELECT * FROM measurements ORDER BY id DESC LIMIT 5;"
```

---

## REST API

Base URL: `http://localhost:5001`

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Health check → `{"status": "ok"}` |
| GET | `/devices` | All devices with online status |
| GET | `/devices/<device_id>` | Status of one device (404 if unknown) |
| GET | `/measurements` | 20 most recent measurements (all devices) |
| GET | `/measurements/latest` | Single most recent measurement (any device/sensor) |
| GET | `/measurements/history` | Filtered history — params: `device_id`, `sensor`, `limit` (default 20), `order` (`asc`/`desc`, default `desc`) |
| GET | `/v2/measurements` | Same data via SQLAlchemy — params: `limit` (default 20), `order` |

Examples:

```bash
curl http://localhost:5001/health
curl http://localhost:5001/devices
curl "http://localhost:5001/measurements/history?device_id=esp32-1C0B58FE8CE0&sensor=core_temperature&limit=10"
```

---

## Desktop dashboard (UI)

### Install and run

```bash
cd ui
pip install -r requirements.txt
python3 main.py
```

Run it from inside `ui/` — imports are resolved relative to that folder.

### Usage

1. Check that the **API URL** is `http://localhost:5001` and click **Test API** (status turns green **OK**).
2. Click **Refresh devices** and select a device.
3. Enter a **Sensor** name (`temperature`, `humidity`, `azimuth` or `core_temperature`) and a **Limit**.
4. Click **Fetch latest** (latest value for that device/sensor) or **Fetch history** (chart + table of recent records).
5. Optionally enable **Auto-refresh** and set the interval.

All requests and errors are listed in the **Diagnostics** panel.

<img width="1110" height="788" alt="preview4" src="https://github.com/user-attachments/assets/cbe6de1d-9f3f-45c1-b636-26518f9921f7" />

---

## Common issues

**ESP32 cannot connect to MQTT** — `MQTT_HOST` in `secrets.h` must be the LAN IP of the Docker host, not `localhost`. Make sure the ESP32 and the host are on the same network and port 1883 is not blocked by a firewall. Check `docker compose logs -f broker`.

**ESP32 stuck on "Oczekiwanie na synchronizacje czasu..."** — the board cannot reach the NTP servers; check internet access on the Wi-Fi network.

**Messages arrive in MQTT but not in the database** — check `docker compose logs -f ingestor` for `Invalid payload` or `Error:` lines.

**API not responding** — check `docker compose logs -f flask` and `docker compose logs -f database`.

---

## CI

A GitHub Actions workflow ([.github/workflows/docker-image.yml](.github/workflows/docker-image.yml)) builds the `flask`, `broker` and `database` images on every push and pull request to `main`.

---

## License

[Apache License 2.0](LICENSE)
