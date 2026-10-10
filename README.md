# Distributed Measurement System

This repository contains a simple measurement system based on ESP32 devices, an MQTT broker, a Flask backend, and a PostgreSQL database. Devices publish data to the broker, the `ingestor` receives messages from MQTT and stores them in the database, and the REST API exposes the data for further use.

## Project structure

- `api/` — Flask REST API backend
- `broker/` — MQTT broker (Mosquitto)
- `database/` — PostgreSQL initialization
- `esp32/` — firmware for ESP32 devices
- `ingestor/` — service that subscribes to MQTT and stores data in the database
- `ui/` — desktop application
- `docs/` — project documentation

---

## Requirements

Before running the project, make sure you have installed:

- Docker
- Docker Compose
- Python 3
- optionally: MQTT Explorer or Mosquitto tools for testing the broker

---

## Quick start

### 1. Clone the repository

```bash
git clone https://github.com/mateuszbartczak-pwr/Rozproszone-systemy-pomiarowe.git
cd Rozproszone-systemy-pomiarowe
```

### 2. Start the environment

```bash
docker compose up -d --build
```

This starts the following containers:

- `api`
- `broker`
- `database`
- `ingestor`

### 3. Check the status

```bash
docker compose ps
```

### 4. View logs

```bash
docker compose logs -f
```

Or only for a specific service:

```bash
docker compose logs -f broker
docker compose logs -f api
docker compose logs -f database
docker compose logs -f ingestor
```

### 5. Stop the environment

```bash
docker compose down
```

---

## Services available after startup

- REST API: http://localhost:5001
- MQTT broker: localhost:1883
- PostgreSQL: localhost:5432

---

## MQTT

In this project version, the MQTT broker is configured to accept anonymous connections.

In [broker/mosquitto.conf](broker/mosquitto.conf), the configuration is:

```conf
allow_anonymous true
listener 1883
```

This means no username or password is required to connect to MQTT.

### Connection parameters

- Host: `localhost`
- Port: `1883`
- Username: empty
- Password: empty

If you are testing the broker locally:

```bash
mosquitto_sub -h localhost -p 1883 -t 'lab/#' -v
```

If you want to check messages from the Docker network, use the host name `broker`:

```bash
mosquitto_sub -h broker -p 1883 -t 'lab/#' -v
```

> This is not a production-safe configuration, but it works correctly for this lab/project setup.

---

## REST API

After starting the backend, the following endpoints are available:

### Application health

```bash
curl http://localhost:5001/health
```

### List devices

```bash
curl http://localhost:5001/devices
```

### Latest measurements

```bash
curl http://localhost:5001/measurements
curl http://localhost:5001/measurements/latest
```

### Measurement history with filters

```bash
curl "http://localhost:5001/measurements/history?device_id=esp32-XXXX&sensor=temperature&limit=10"
```

---

## Running the UI

The desktop application is located in the `ui/` directory and is best launched from that folder, because imports are resolved relative to files in that directory.

```bash
cd ui
python3 main.py
```

If you run the project from the repository root, use:

```bash
cd /home/marta/Desktop/repos/Rozproszone-systemy-pomiarowe/ui
python3 main.py
```

---

## Example MQTT topics

MQTT topics usually follow this structure:

```text
lab/{group_id}/{device_id}/{sensor}
```

Example:

```text
lab/g05/esp32-1234/temperature
```

Measurement data is stored in the `measurements` table, and device status values are stored in the `device_status` table.

---

## Database

Once the PostgreSQL container is running, the database is available with the following parameters:

- host: `localhost`
- port: `5432`
- user: `admin`
- password: `admin_pass1234`
- database: `abcd_db`

The initialization scripts are located in:

- `database/01-init_database.sql`

---

## ESP32

The ESP32 firmware publishes data to MQTT and creates topics using this format:

```cpp
lab/{MQTT_GROUP}/{deviceId}/{sensor}
```

Wi‑Fi and MQTT parameters are configured in:

- `esp32/include/secrets.h`

---

## Common issues

### 1. `python3 main.py` does not work from the repository root

Run the UI from the `ui/` folder:

```bash
cd ui
python3 main.py
```

### 2. No MQTT connection

Check the broker logs:

```bash
docker compose logs -f broker
```

Make sure you are using port `1883` and that the username/password fields are empty.

### 3. API not responding

Check the logs for the backend and database:

```bash
docker compose logs -f api
docker compose logs -f database
```

---

## Project goal

The goal of this project is to build a distributed measurement system in which devices collect data from sensors, send it via MQTT, store it in a database, and expose it through an API and a user interface.

The project is developed in stages and can be extended with additional modules, security features, and further functionality.
