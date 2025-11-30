# 🚀 Schnellstart: LLM-Upgrade

## In 3 Schritten zu besserer KI

### 1️⃣ Konfiguration erstellen

```bash
cd /home/ubuntu/Jarvis

# Kopiere die Beispiel-Konfiguration
cp .env.example config/.env

# Bearbeite die Datei (optional - funktioniert auch ohne Änderungen)
nano config/.env
```

**Wichtig:** Der `OPENAI_API_KEY` ist bereits vom System konfiguriert! Du musst nichts ändern.

### 2️⃣ Services starten

```bash
# Stoppe alte Services
docker-compose down

# Baue neue Services
docker-compose build llm_gateway orchestrator

# Starte alles
docker-compose up -d

# Warte ~30 Sekunden, dann prüfe Status
docker-compose ps
```

### 3️⃣ Testen

```bash
# Health Check
curl http://localhost:8007/health

# Test-Anfrage
curl -X POST http://localhost:8003/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query":"Erkläre mir in einem Satz, was du jetzt besser kannst als vorher."}'
```

## ✅ Fertig!

Dein JARVIS nutzt jetzt **gpt-4.1-mini** als primäres Modell mit automatischem Fallback zu lokalem Ollama.

### Was ist neu?

- 🧠 **Deutlich intelligentere Antworten**
- 💬 **Natürlichere Konversation**
- 🔄 **Automatisches Fallback** bei API-Problemen
- ⚙️ **Einfacher Provider-Wechsel** per Umgebungsvariable

### Verfügbare Modelle

In `config/.env` kannst du wählen:

```bash
# Schnell & günstig (Standard)
PRIMARY_LLM_MODEL=gpt-4.1-mini

# Sehr schnell & sehr günstig
PRIMARY_LLM_MODEL=gpt-4.1-nano

# Google Gemini
PRIMARY_LLM_MODEL=gemini-2.5-flash

# Nur lokales Ollama (keine API)
PRIMARY_LLM_PROVIDER=ollama
PRIMARY_LLM_MODEL=llama3.1
```

Nach Änderungen:
```bash
docker-compose restart llm_gateway orchestrator
```

## 🎯 Nächste Schritte

Siehe `LLM_UPGRADE_README.md` für:
- Detaillierte Konfiguration
- Troubleshooting
- Kosten-Übersicht
- Erweiterte Features

**Viel Spaß mit deinem upgegradeten JARVIS!** 🎉
