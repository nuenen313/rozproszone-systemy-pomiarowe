#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include "secrets.h"
#include "sensorsim.h"
#include <time.h>
#include <sys/time.h>
#include <Preferences.h>
#include <map>

WiFiClient espClient;
PubSubClient mqttClient(espClient);
String deviceId;
String topic;
String topicCurrent;
Preferences prefs;
std::map<String, uint32_t> seqMap;

long long getTimestampMs();
String generateDeviceIdFromEfuse() {
    uint64_t chipId = ESP.getEfuseMac();
    char id[32];
    snprintf(id, sizeof(id), "esp32-%04X%08X",
    (uint16_t)(chipId >> 32),
    (uint32_t)chipId);
    return String(id);
}
void connectWiFi() {
    Serial.print("Laczenie z Wi-Fi: ");
    Serial.println(WIFI_SSID);
    WiFi.mode(WIFI_STA);
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
        while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    Serial.println();
    Serial.println("Polaczono z Wi-Fi");
    Serial.print("Adres IP: ");
    Serial.println(WiFi.localIP());
}
void connectMQTT() {
    mqttClient.setServer(MQTT_HOST, MQTT_PORT);
    while (!mqttClient.connected()) {
        Serial.print("Laczenie z MQTT...");
        if (mqttClient.connect(deviceId.c_str())) {
            Serial.println("OK");
        } else {
            Serial.print("blad, rc=");
            Serial.print(mqttClient.state());
            Serial.println(" - ponowna proba za 2 s");
            delay(2000);
        }
    }
}

long long getTimestampMs() {
    struct timeval tv;
    gettimeofday(&tv, NULL);
    return ((long long)tv.tv_sec * 1000LL) + (tv.tv_usec / 1000);
}

void publishStatusTopic(String status) {
    String topicStatus = topic + "status";
    mqttClient.publish(topicStatus.c_str(), status.c_str());
    Serial.print("Publikacja statusu na topic: ");
    Serial.println(topicStatus);   
    Serial.println(status);
}

void publishMeasurement(String sensor, float sensorValue, String unit) {
    JsonDocument doc;
    doc["schema_version"] = "1.0"; //na razie hard coded
    doc["device_id"] = deviceId;
    doc["sensor"] = sensor;
    doc["value"] = sensorValue;
    doc["unit"] = unit;
    doc["ts_ms"] = getTimestampMs();
    topicCurrent = topic + sensor;
    uint32_t currentSeq = ++seqMap[topicCurrent];
    doc["seq"] = currentSeq;
    char payload[256];
    serializeJson(doc, payload);
    mqttClient.publish(topicCurrent.c_str(), payload);
    Serial.print("Publikacja na topic: ");
    Serial.println(topicCurrent);   
    Serial.println(payload);
}

void setup() {
    Serial.begin(115200);
    delay(2000);
    prefs.begin("app", false);

    deviceId = prefs.getString("device_id", "");
    Serial.println("Odczyt device ID z flash: " + deviceId);
    if (deviceId == "") {
        deviceId = generateDeviceIdFromEfuse();
        prefs.putString("device_id", deviceId);
        Serial.println("Zapisano do flash nowy device ID: " + deviceId);
    } else {
        Serial.println("Odczytano device ID z pamięci: " + deviceId);
    }
    delay(2000);

    topic = "lab/" + String(MQTT_GROUP) + "/" + deviceId + "/";
    Serial.print("Device ID: ");
    Serial.println(deviceId);
    connectWiFi();
    configTime(0, 0, "pool.ntp.org", "time.nist.gov");
    struct tm timeinfo;
    while (!getLocalTime(&timeinfo)) {
        Serial.println("Oczekiwanie na synchronizacje czasu...");
        delay(500);
    }
    Serial.println("Czas zsynchronizowany.");
    connectMQTT();
}
void loop() {
    if (WiFi.status() != WL_CONNECTED) {
        connectWiFi();
    }
    long long ts_ms = getTimestampMs();
    Serial.println(ts_ms);
    if (!mqttClient.connected()) {
        connectMQTT();
    }
    else {
        publishStatusTopic("online");
    }
    mqttClient.loop();
    publishMeasurement("temperature", getSimTemperature(), "C");
    publishMeasurement("humidity", getSimHumidity(), "%");
    publishMeasurement("azimuth", getSimAzimuth(), "deg");
    publishMeasurement("core_temperature", getRealCoreTemperature(), "C");
    delay(5000);
}