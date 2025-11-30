# JARVIS Smart Home Integration

Diese Dokumentation beschreibt die Smart Home Integration für JARVIS, die es ermöglicht, Home Assistant Geräte über natürliche Sprache zu steuern.

## Inhaltsverzeichnis

1. [Architektur-Übersicht](#architektur-übersicht)
2. [Setup-Anleitung](#setup-anleitung)
3. [API-Dokumentation](#api-dokumentation)
4. [Verwendungsbeispiele](#verwendungsbeispiele)
5. [Troubleshooting](#troubleshooting)

## Architektur-Übersicht

Die Smart Home Integration besteht aus mehreren Komponenten, die nahtlos zusammenarbeiten:

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│    Frontend     │────▶│   Orchestrator  │────▶│   LLM Gateway   │
│   (React/TS)    │     │    (FastAPI)    │     │    (FastAPI)    │
└─────────────────┘     └────────┬────────┘     └─────────────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │   Toolserver    │
                        │    (FastAPI)    │
                        └────────┬────────┘
                                 │
                                 ▼
                        ┌─────────────────┐     ┌─────────────────┐
                        │   Smart Home    │────▶│ Home Assistant  │
                        │    Service      │     │     (extern)    │
                        │    (FastAPI)    │◀────│                 │
                        └─────────────────┘     └─────────────────┘
                              WebSocket
```

### Komponenten

Der **Smart Home Service** (`services/smarthome`) ist ein neuer Microservice, der als Abstraktionsschicht zwischen JARVIS und Home Assistant fungiert. Er bietet eine REST API für Gerätesteuerung und eine WebSocket-Verbindung für Echtzeit-Updates.

Der **Toolserver** (`services/toolserver`) wurde um vier neue Smart Home Tools erweitert, die das LLM nutzen kann, um Geräte zu steuern und Zustände abzufragen.

Der **Orchestrator** (`services/orchestrator`) wurde erweitert, um die neuen Smart Home Tool-Aufrufe zu parsen und auszuführen.

### Datenfluss

Wenn ein Benutzer eine Anfrage wie "Schalte das Licht in der Küche ein" stellt, durchläuft die Anfrage folgende Schritte:

1. Die Anfrage geht vom Frontend zum Orchestrator
2. Der Orchestrator sendet die Anfrage an das LLM Gateway
3. Das LLM erkennt die Absicht und ruft das passende Tool auf
4. Der Orchestrator führt den Tool-Call über den Toolserver aus
5. Der Toolserver kommuniziert mit dem Smart Home Service
6. Der Smart Home Service steuert das Gerät über die Home Assistant API
7. Das Ergebnis wird zurück an das LLM gesendet
8. Das LLM formuliert eine natürliche Antwort für den Benutzer

## Setup-Anleitung

### Voraussetzungen

- Docker und Docker Compose installiert
- Home Assistant Instanz (lokal oder remote)
- Netzwerkzugriff von JARVIS zu Home Assistant

### Schritt 1: Long-Lived Access Token erstellen

1. Öffne Home Assistant in deinem Browser
2. Klicke auf dein Profil (unten links)
3. Scrolle nach unten zu "Long-Lived Access Tokens"
4. Klicke auf "Token erstellen"
5. Gib einen Namen ein (z.B. "JARVIS")
6. Kopiere den generierten Token (wird nur einmal angezeigt!)

### Schritt 2: Umgebungsvariablen konfigurieren

Bearbeite die Datei `config/.env` und füge folgende Variablen hinzu:

```bash
# Smart Home Integration (Home Assistant)
HOME_ASSISTANT_URL=http://homeassistant.local:8123
HOME_ASSISTANT_TOKEN=dein_long_lived_access_token_hier
```

Ersetze `homeassistant.local` mit der IP-Adresse oder dem Hostnamen deiner Home Assistant Instanz und füge deinen Token ein.

### Schritt 3: Services starten

```bash
docker-compose up -d --build
```

### Schritt 4: Verbindung testen

Prüfe, ob der Smart Home Service läuft:

```bash
curl http://localhost:8008/health
```

Erwartete Antwort bei erfolgreicher Verbindung:
```json
{"status": "healthy", "home_assistant": "connected"}
```

## API-Dokumentation

### Smart Home Service Endpunkte

Der Smart Home Service läuft auf Port 8008 und bietet folgende Endpunkte:

#### GET /health

Prüft die Verbindung zu Home Assistant.

**Response (Erfolg):**
```json
{
  "status": "healthy",
  "home_assistant": "connected"
}
```

**Response (Fehler):**
```json
{
  "detail": "Cannot connect to Home Assistant"
}
```

#### GET /v1/entities

Ruft alle relevanten Entitäten von Home Assistant ab.

**Query Parameter:**
- `domain` (optional): Filtert nach Gerätetyp (z.B. "light", "switch", "sensor")

**Response:**
```json
[
  {
    "entity_id": "light.wohnzimmer",
    "state": "on",
    "friendly_name": "Wohnzimmer Licht",
    "attributes": {
      "brightness": 255,
      "color_mode": "brightness"
    },
    "last_changed": "2024-01-15T10:30:00+00:00",
    "last_updated": "2024-01-15T10:30:00+00:00"
  }
]
```

#### GET /v1/entities/{entity_id}

Ruft den Zustand einer einzelnen Entität ab.

**Response:**
```json
{
  "entity_id": "sensor.temperatur_aussen",
  "state": "21.5",
  "friendly_name": "Aussentemperatur",
  "attributes": {
    "unit_of_measurement": "°C",
    "device_class": "temperature"
  }
}
```

#### POST /v1/services/{domain}/{service}

Ruft einen Home Assistant Service auf.

**Request Body:**
```json
{
  "entity_id": "light.wohnzimmer",
  "data": {
    "brightness": 128
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Service light.turn_on called successfully",
  "entity_id": "light.wohnzimmer"
}
```

#### POST /v1/actions/turn_on

Schaltet ein Gerät ein.

**Request Body:**
```json
{
  "entity_id": "light.wohnzimmer"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Turned on light.wohnzimmer",
  "entity_id": "light.wohnzimmer"
}
```

#### POST /v1/actions/turn_off

Schaltet ein Gerät aus.

**Request Body:**
```json
{
  "entity_id": "light.wohnzimmer"
}
```

#### POST /v1/actions/toggle

Wechselt den Zustand eines Geräts.

**Request Body:**
```json
{
  "entity_id": "switch.steckdose_1"
}
```

### Verfügbare LLM Tools

Das LLM kann folgende Tools für die Smart Home Steuerung nutzen:

#### smarthome_list_devices

Listet alle verfügbaren Geräte eines bestimmten Typs auf.

**Parameter:**
- `domain`: Gerätetyp (z.B. "light", "switch", "sensor", "media_player")

**Beispiel-Aufruf:**
```
<tool_call>smarthome_list_devices("light")</tool_call>
```

#### smarthome_turn_on

Schaltet ein Gerät ein.

**Parameter:**
- `entity_id`: Die Entity-ID des Geräts

**Beispiel-Aufruf:**
```
<tool_call>smarthome_turn_on("light.wohnzimmer")</tool_call>
```

#### smarthome_turn_off

Schaltet ein Gerät aus.

**Parameter:**
- `entity_id`: Die Entity-ID des Geräts

**Beispiel-Aufruf:**
```
<tool_call>smarthome_turn_off("light.wohnzimmer")</tool_call>
```

#### smarthome_get_status

Fragt den aktuellen Zustand eines Geräts oder Sensors ab.

**Parameter:**
- `entity_id`: Die Entity-ID des Geräts oder Sensors

**Beispiel-Aufruf:**
```
<tool_call>smarthome_get_status("sensor.temperatur_aussen")</tool_call>
```

## Verwendungsbeispiele

### Beispiel 1: Licht einschalten

**Benutzer:** "JARVIS, schalte bitte das Licht im Wohnzimmer ein."

**JARVIS Verarbeitung:**
1. LLM erkennt die Absicht "Gerät einschalten"
2. LLM ruft `smarthome_list_devices("light")` auf, um verfügbare Lichter zu finden
3. LLM findet `light.wohnzimmer` mit dem Namen "Wohnzimmer Licht"
4. LLM ruft `smarthome_turn_on("light.wohnzimmer")` auf
5. Gerät wird eingeschaltet

**JARVIS Antwort:** "Verstanden. Ich habe das Wohnzimmer Licht eingeschaltet."

### Beispiel 2: Temperatur abfragen

**Benutzer:** "Wie warm ist es draussen?"

**JARVIS Verarbeitung:**
1. LLM erkennt die Absicht "Temperatur abfragen"
2. LLM ruft `smarthome_list_devices("sensor")` auf
3. LLM findet `sensor.temperatur_aussen` mit device_class "temperature"
4. LLM ruft `smarthome_get_status("sensor.temperatur_aussen")` auf
5. Erhält: "Die Temperatur (Aussentemperatur) beträgt 21.5°C"

**JARVIS Antwort:** "Die Aussentemperatur beträgt aktuell 21.5 Grad Celsius."

### Beispiel 3: Mehrere Geräte steuern

**Benutzer:** "Schalte alle Lichter im Erdgeschoss aus."

**JARVIS Verarbeitung:**
1. LLM ruft `smarthome_list_devices("light")` auf
2. LLM identifiziert alle Lichter im Erdgeschoss anhand der Namen
3. LLM ruft `smarthome_turn_off()` für jedes relevante Licht auf
4. Alle Geräte werden ausgeschaltet

**JARVIS Antwort:** "Ich habe alle Lichter im Erdgeschoss ausgeschaltet: Wohnzimmer, Küche und Flur."

### Beispiel 4: Gerätestatus prüfen

**Benutzer:** "Ist das Licht in der Küche an?"

**JARVIS Verarbeitung:**
1. LLM ruft `smarthome_get_status("light.kuechenlicht")` auf
2. Erhält: "Küchenlicht ist eingeschaltet mit 80% Helligkeit"

**JARVIS Antwort:** "Ja, das Küchenlicht ist eingeschaltet und hat eine Helligkeit von 80%."

## Troubleshooting

### Problem: "HOME_ASSISTANT_TOKEN not configured"

**Ursache:** Der Home Assistant Token wurde nicht in der Konfiguration hinterlegt.

**Lösung:**
1. Erstelle einen Long-Lived Access Token in Home Assistant
2. Füge den Token in `config/.env` ein
3. Starte die Services neu: `docker-compose restart smarthome toolserver`

### Problem: "Cannot connect to Home Assistant"

**Ursache:** Der Smart Home Service kann Home Assistant nicht erreichen.

**Lösungen:**
1. Prüfe, ob Home Assistant läuft und erreichbar ist
2. Prüfe die `HOME_ASSISTANT_URL` in der Konfiguration
3. Stelle sicher, dass die Firewall den Zugriff erlaubt
4. Bei Docker: Prüfe, ob das Netzwerk korrekt konfiguriert ist

```bash
# Teste die Verbindung vom Container aus
docker exec jarvis-smarthome curl -s http://homeassistant.local:8123/api/ \
  -H "Authorization: Bearer $HOME_ASSISTANT_TOKEN"
```

### Problem: "Invalid Home Assistant token"

**Ursache:** Der Token ist ungültig oder abgelaufen.

**Lösung:**
1. Erstelle einen neuen Long-Lived Access Token in Home Assistant
2. Aktualisiere den Token in `config/.env`
3. Starte die Services neu

### Problem: "Entity not found"

**Ursache:** Die angegebene Entity-ID existiert nicht in Home Assistant.

**Lösungen:**
1. Prüfe die korrekte Schreibweise der Entity-ID
2. Nutze `smarthome_list_devices()` um verfügbare Geräte zu sehen
3. Prüfe in Home Assistant, ob das Gerät korrekt eingerichtet ist

### Problem: "Smart Home Service nicht erreichbar"

**Ursache:** Der Toolserver kann den Smart Home Service nicht erreichen.

**Lösungen:**
1. Prüfe, ob der Smart Home Service läuft: `docker ps | grep smarthome`
2. Prüfe die Logs: `docker logs jarvis-smarthome`
3. Stelle sicher, dass beide Services im gleichen Docker-Netzwerk sind

### Problem: WebSocket-Verbindung fehlgeschlagen

**Ursache:** Die WebSocket-Verbindung zu Home Assistant konnte nicht hergestellt werden.

**Hinweis:** Die WebSocket-Verbindung ist optional und wird für Echtzeit-Updates verwendet. Der Service funktioniert auch ohne WebSocket-Verbindung.

**Lösungen:**
1. Prüfe, ob Home Assistant WebSocket-Verbindungen erlaubt
2. Prüfe die Logs: `docker logs jarvis-smarthome | grep WebSocket`
3. Bei Proxy-Nutzung: Stelle sicher, dass WebSocket-Verbindungen durchgelassen werden

### Logs einsehen

```bash
# Smart Home Service Logs
docker logs -f jarvis-smarthome

# Toolserver Logs
docker logs -f jarvis-toolserver

# Orchestrator Logs
docker logs -f jarvis-orchestrator
```

## Unterstützte Gerätetypen

Der Smart Home Service unterstützt folgende Home Assistant Domains:

| Domain | Beschreibung | Beispiel-Aktionen |
|--------|--------------|-------------------|
| `light` | Lichter | Ein/Aus, Helligkeit |
| `switch` | Schalter | Ein/Aus |
| `sensor` | Sensoren | Status abfragen |
| `binary_sensor` | Binäre Sensoren | Status abfragen |
| `media_player` | Mediaplayer | Status abfragen |
| `climate` | Klimageräte | Status abfragen |
| `cover` | Rollläden/Jalousien | Öffnen/Schliessen |
| `fan` | Ventilatoren | Ein/Aus |

## Zukünftige Erweiterungen

Die WebSocket-Verbindung zum Home Assistant ist bereits implementiert und loggt Zustandsänderungen. Diese Funktionalität wird in zukünftigen Versionen vom Proactivity-Service genutzt, um proaktiv auf Ereignisse zu reagieren (z.B. "Das Licht im Flur wurde eingeschaltet").

Geplante Features:
- Proaktive Benachrichtigungen bei Zustandsänderungen
- Szenen und Automationen steuern
- Erweiterte Gerätesteuerung (Helligkeit, Farbe, Temperatur)
- Sprachgesteuerte Routinen
