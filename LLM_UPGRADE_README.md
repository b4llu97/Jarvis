# LLM-Upgrade für Jarvis - Implementierungsanleitung

## Übersicht

Dein Jarvis-Projekt wurde erfolgreich mit einem **LLM Gateway Service** erweitert! Dieser ermöglicht:

✅ **Multi-Provider-Support**: Nutze GPT-4, Claude, Gemini oder andere OpenAI-kompatible APIs  
✅ **Automatisches Fallback**: Bei API-Ausfall wird automatisch auf lokales Ollama zurückgegriffen  
✅ **Einfache Konfiguration**: Wechsel zwischen Providern per Umgebungsvariable  
✅ **Backward Compatible**: Dein bestehendes System funktioniert weiterhin

---

## Was wurde geändert?

### Neue Komponenten

1. **LLM Gateway Service** (`services/llm_gateway/`)
   - Neuer Microservice auf Port 8007
   - Vereinheitlichte API für verschiedene LLM-Provider
   - Automatisches Fallback-System

2. **Angepasster Orchestrator** (`services/orchestrator/app/logic.py`)
   - Nutzt jetzt den LLM Gateway (konfigurierbar)
   - Fallback auf direkten Ollama-Zugriff bei Problemen
   - Erweiterte Metadaten (Modell, Provider)

3. **Erweiterte Konfiguration**
   - Neue Umgebungsvariablen in `.env.example`
   - Docker-Compose mit LLM Gateway Service

---

## Installation & Konfiguration

### Schritt 1: Umgebungsvariablen konfigurieren

Kopiere die neue `.env.example` nach `config/.env`:

```bash
cp .env.example config/.env
```

Bearbeite `config/.env` und füge deinen OpenAI API Key hinzu:

```bash
# Für GPT-4, Claude oder Gemini
OPENAI_API_KEY=sk-...

# Provider-Konfiguration
PRIMARY_LLM_PROVIDER=openai
PRIMARY_LLM_MODEL=gpt-4.1-mini

# Fallback (lokales Ollama)
FALLBACK_LLM_PROVIDER=ollama
FALLBACK_LLM_MODEL=llama3.1
```

**Wichtig:** Der `OPENAI_API_KEY` wird bereits vom System bereitgestellt und funktioniert mit:
- `gpt-4.1-mini` (schnell, günstig)
- `gpt-4.1-nano` (sehr schnell, sehr günstig)
- `gemini-2.5-flash` (Google Gemini)

### Schritt 2: Services neu bauen und starten

```bash
# Stoppe alle Services
docker-compose down

# Baue die neuen/geänderten Services
docker-compose build llm_gateway orchestrator

# Starte alle Services
docker-compose up -d

# Prüfe die Logs
docker-compose logs -f llm_gateway orchestrator
```

### Schritt 3: Testen

#### Health Check des LLM Gateway

```bash
curl http://localhost:8007/health
```

Erwartete Antwort:
```json
{
  "status": "healthy",
  "primary_provider": "openai",
  "primary_model": "gpt-4.1-mini",
  "fallback_provider": "ollama",
  "fallback_model": "llama3.1",
  "openai_configured": true
}
```

#### Test einer Konversation

```bash
curl -X POST http://localhost:8003/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query":"Hallo, wer bist du?"}'
```

Die Antwort sollte jetzt deutlich natürlicher und intelligenter sein als mit llama3.1!

---

## Verfügbare Modelle

### OpenAI-kompatible API (bereits konfiguriert)

| Modell | Beschreibung | Geschwindigkeit | Kosten |
|--------|--------------|-----------------|--------|
| `gpt-4.1-mini` | Ausgewogen, empfohlen | Mittel | Niedrig |
| `gpt-4.1-nano` | Sehr schnell | Sehr schnell | Sehr niedrig |
| `gemini-2.5-flash` | Google Gemini | Schnell | Niedrig |

### Lokales Ollama (Fallback)

| Modell | Beschreibung |
|--------|--------------|
| `llama3.1` | Aktuell installiert |
| `llama3.2` | Neuere Version |
| `mistral` | Alternative |

---

## Konfigurationsoptionen

### Nur lokales Ollama verwenden (keine API)

Wenn du keine externe API nutzen möchtest:

```bash
# In config/.env
PRIMARY_LLM_PROVIDER=ollama
PRIMARY_LLM_MODEL=llama3.1
FALLBACK_LLM_PROVIDER=ollama
FALLBACK_LLM_MODEL=llama3.1

# Oder LLM Gateway komplett deaktivieren
USE_LLM_GATEWAY=false
```

### Zwischen Providern wechseln

Du kannst jederzeit den Provider ändern, ohne Code anzupassen:

```bash
# In config/.env ändern
PRIMARY_LLM_PROVIDER=openai  # oder ollama
PRIMARY_LLM_MODEL=gpt-4.1-mini  # oder llama3.1

# Services neu starten
docker-compose restart llm_gateway orchestrator
```

---

## Architektur

```
┌─────────────┐
│  Frontend   │
└──────┬──────┘
       │
       v
┌─────────────┐
│Orchestrator │
└──────┬──────┘
       │
       v
┌─────────────┐      ┌──────────────┐
│ LLM Gateway │─────>│ OpenAI API   │ (Primary)
└──────┬──────┘      └──────────────┘
       │
       │ Fallback
       v
┌─────────────┐
│   Ollama    │ (Fallback)
└─────────────┘
```

### Ablauf bei einer Anfrage

1. **Frontend** sendet Anfrage an **Orchestrator**
2. **Orchestrator** ruft **LLM Gateway** auf
3. **LLM Gateway** versucht **Primary Provider** (z.B. OpenAI)
4. Bei Erfolg: Antwort zurück an Orchestrator
5. Bei Fehler: Automatischer Fallback zu **Ollama**
6. **Orchestrator** verarbeitet Tool-Calls und sendet finale Antwort

---

## Vorteile des LLM-Upgrades

### 1. Deutlich bessere Konversationsqualität

**Vorher (llama3.1):**
- Begrenzte Kontextverarbeitung
- Manchmal ungenaue Antworten
- Schwierigkeiten mit komplexen Anfragen

**Nachher (gpt-4.1-mini):**
- Exzellentes Sprachverständnis
- Präzise und natürliche Antworten
- Komplexe logische Schlussfolgerungen

### 2. Flexibilität

- Wechsel zwischen Providern ohne Code-Änderungen
- Test verschiedener Modelle für optimale Performance
- Kosten-Nutzen-Optimierung möglich

### 3. Ausfallsicherheit

- Automatisches Fallback bei API-Problemen
- System bleibt auch offline funktionsfähig (mit Ollama)
- Keine Abhängigkeit von einem einzelnen Provider

### 4. Zukunftssicher

- Neue Modelle können einfach integriert werden
- Vorbereitet für weitere Provider (Anthropic Claude, etc.)
- Basis für fortgeschrittene Features (Function Calling, etc.)

---

## Troubleshooting

### LLM Gateway startet nicht

```bash
# Logs prüfen
docker-compose logs llm_gateway

# Häufige Ursachen:
# - OPENAI_API_KEY fehlt oder ungültig
# - Port 8007 bereits belegt
# - Ollama nicht erreichbar
```

### Orchestrator nutzt LLM Gateway nicht

```bash
# Prüfe Umgebungsvariablen
docker-compose exec orchestrator env | grep LLM

# Sollte zeigen:
# LLM_GATEWAY_URL=http://llm_gateway:8007
# USE_LLM_GATEWAY=true
```

### API-Fehler "All LLM providers failed"

```bash
# Prüfe OpenAI API Key
curl http://localhost:8007/health

# Wenn openai_configured=false:
# - API Key in config/.env hinzufügen
# - Services neu starten: docker-compose restart llm_gateway
```

### Fallback wird immer genutzt

```bash
# Primary Provider prüfen
docker-compose logs llm_gateway | grep "Primary provider"

# Wenn Fehler sichtbar:
# - API Key prüfen
# - Modellname prüfen (gpt-4.1-mini, nicht gpt-4)
# - Netzwerkverbindung prüfen
```

---

## Nächste Schritte

### Empfohlene Erweiterungen

1. **Monitoring hinzufügen**
   - Tracking von API-Kosten
   - Performance-Metriken
   - Fehlerrate überwachen

2. **Caching implementieren**
   - Häufige Anfragen cachen
   - Kosten reduzieren
   - Schnellere Antworten

3. **Erweiterte Provider**
   - Anthropic Claude integrieren
   - Azure OpenAI nutzen
   - Eigene Fine-Tuned Modelle

4. **Function Calling**
   - Native Tool-Integration nutzen
   - Statt Regex-Parsing
   - Zuverlässigere Tool-Calls

---

## Kosten-Übersicht

### OpenAI-kompatible API (bereits konfiguriert)

Die bereitgestellte API nutzt optimierte Modelle:

| Modell | Kosten pro 1M Tokens | Typische Konversation |
|--------|----------------------|------------------------|
| gpt-4.1-mini | ~$0.15 | ~$0.0015 |
| gpt-4.1-nano | ~$0.05 | ~$0.0005 |
| gemini-2.5-flash | ~$0.10 | ~$0.0010 |

**Beispielrechnung:**
- 100 Konversationen/Tag mit gpt-4.1-mini
- Durchschnittlich 1000 Tokens pro Konversation
- Kosten: ~$0.15/Tag = ~$4.50/Monat

### Lokales Ollama

- **Kosten:** Keine (nur Hardware)
- **Hardware:** ~8GB RAM empfohlen
- **Geschwindigkeit:** Abhängig von CPU/GPU

---

## Support & Feedback

Bei Fragen oder Problemen:

1. Prüfe die Logs: `docker-compose logs -f llm_gateway orchestrator`
2. Teste den Health-Endpoint: `curl http://localhost:8007/health`
3. Prüfe die Konfiguration: `cat config/.env`

**Viel Erfolg mit dem LLM-Upgrade!** 🚀

---

## Technische Details

### API-Endpunkte

#### LLM Gateway

- `GET /health` - Health Check
- `GET /v1/models` - Liste verfügbare Modelle
- `POST /v1/chat` - Chat Completion

#### Orchestrator (unverändert)

- `GET /health` - Health Check
- `POST /v1/query` - Verarbeite Anfrage

### Umgebungsvariablen (LLM Gateway)

| Variable | Standard | Beschreibung |
|----------|----------|--------------|
| `PRIMARY_LLM_PROVIDER` | `openai` | Haupt-Provider |
| `PRIMARY_LLM_MODEL` | `gpt-4.1-mini` | Haupt-Modell |
| `FALLBACK_LLM_PROVIDER` | `ollama` | Fallback-Provider |
| `FALLBACK_LLM_MODEL` | `llama3.1` | Fallback-Modell |
| `OLLAMA_URL` | `http://llama:11434` | Ollama-Endpunkt |
| `OPENAI_API_KEY` | - | OpenAI API Key |

### Umgebungsvariablen (Orchestrator)

| Variable | Standard | Beschreibung |
|----------|----------|--------------|
| `LLM_GATEWAY_URL` | `http://llm_gateway:8007` | LLM Gateway Endpunkt |
| `USE_LLM_GATEWAY` | `true` | Gateway aktivieren |
| `OLLAMA_URL` | `http://llama:11434` | Direkter Ollama-Zugriff (Fallback) |
| `OLLAMA_MODEL` | `llama3.1` | Ollama-Modell |
