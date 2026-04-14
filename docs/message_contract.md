### Opis struktury topiców
Ogólna struktura topiców wygląda następująco:

```
lab/<group_id>/<device_id>/<sensor>
```
Dla topiców statusowych przewidziano osobną strukturę, tj.:
```
lab/<group_id>/<device_id>/status
```

### Opis wiadomości JSON (v1)

Wiadomości JSON zawierają dane pomiarowe z czujników. Aktualna wersja schematu to 1.0. Wiadomości są publikowane na topicach typu `lab/<group_id>/<device_id>/<sensor>`.

### Lista pól wymaganych

- `schema_version` (string): Wersja schematu wiadomości, zawsze ustawiona na "1.0"
- `device_id` (string): Unikalny identyfikator urządzenia (np. "esp32-ABCD1234")
- `sensor` (string): Nazwa czujnika (np. "temperature", "humidity", "azimuth")
- `sensor_value` (number): Wartość pomiaru (liczba zmiennoprzecinkowa)
- `unit` (string): Jednostka pomiaru (np. "C", "%", "deg")
- `ts_ms` (integer): Znacznik czasu w milisekundach (Unix timestamp * 1000)
- `seq` (integer): Numer sekwencyjny dla danego czujnika (zwiększany przy każdym pomiarze)

### Lista pól opcjonalnych

Brak pól opcjonalnych. Wszystkie pola są wymagane.

### Podstawowe reguły walidacji

- `schema_version` musi dokładnie równać się "1.0"
- `device_id` nie może być pustym ciągiem znaków
- `sensor` nie może być pustym ciągiem znaków
- `sensor_value` musi być prawidłową liczbą (float)
- `unit` nie może być pustym ciągiem znaków
- `ts_ms` musi być dodatnią liczbą całkowitą (większą od 0)
- `seq` musi być nieujemną liczbą całkowitą (większą lub równą 0)

### Przykład wiadomości poprawnej

```json
{
  "schema_version": "1.0",
  "device_id": "esp32-ABCD1234",
  "sensor": "temperature",
  "sensor_value": 25.5,
  "unit": "C",
  "ts_ms": 1640995200000,
  "seq": 1
}
```

### Przykłady wiadomości błędnych

1. **Brak wymaganego pola `schema_version`:**
   ```json
   {
     "device_id": "esp32-ABCD1234",
     "sensor": "temperature",
     "sensor_value": 25.5,
     "unit": "C",
     "ts_ms": 1640995200000,
     "seq": 1
   }
   ```

2. **Nieprawidłowy typ pola `sensor_value` (ciąg znaków zamiast liczby):**
   ```json
   {
     "schema_version": "1.0",
     "device_id": "esp32-ABCD1234",
     "sensor": "temperature",
     "sensor_value": "25.5",
     "unit": "C",
     "ts_ms": 1640995200000,
     "seq": 1
   }
   ```

3. **Ujemny znacznik czasu:**
   ```json
   {
     "schema_version": "1.0",
     "device_id": "esp32-ABCD1234",
     "sensor": "temperature",
     "sensor_value": 25.5,
     "unit": "C",
     "ts_ms": -1640995200000,
     "seq": 1
   }
   ```