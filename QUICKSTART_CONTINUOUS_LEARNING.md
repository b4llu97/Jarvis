# 🧠 Schnellstart: Kontinuierliches Lernen

## In 3 Schritten zu einem lernenden JARVIS

### 1️⃣ Services aktualisieren

```bash
cd /home/ubuntu/Jarvis

# Backend neu bauen
docker-compose build toolserver orchestrator frontend

# Services neu starten
docker-compose up -d

# Status prüfen (~30 Sekunden warten)
docker-compose ps
```

### 2️⃣ Testen

```bash
# API Health Check
curl http://localhost:8002/health

# Statistiken abrufen (sollte leer sein)
curl http://localhost:8002/v1/learning/statistics
```

Erwartete Antwort:
```json
{
  "total_feedback": 0,
  "average_rating": 0,
  "rating_distribution": {},
  "total_corrections": 0,
  "recent_feedback_7d": 0
}
```

### 3️⃣ Im Browser nutzen

1. Öffne http://localhost:8080
2. Stelle eine Frage an Jarvis
3. Nach der Antwort siehst du 3 Buttons:
   - 👍 **Hilfreich** - Positive Bewertung
   - 👎 **Nicht hilfreich** - Negative Bewertung
   - 💬 **Korrigieren** - Richtige Antwort eingeben
4. Klicke auf **"Lernen"** Tab um Statistiken zu sehen

## ✅ Fertig!

Jarvis lernt jetzt aus deinem Feedback! 🎉

### Was passiert im Hintergrund?

1. **Feedback wird gespeichert** in SQLite-Datenbank
2. **Learning Context** wird bei jeder Anfrage geladen
3. **Korrekturen werden integriert** in System-Prompt
4. **LLM berücksichtigt** Feedback bei Antworten

### Beispiel-Workflow

```
1. Du fragst: "Hauptstadt von Frankreich?"
2. Jarvis antwortet: "London" (falsch!)
3. Du klickst "Korrigieren"
4. Du gibst ein: "Paris"
5. Korrektur wird gespeichert

Nächstes Mal:
1. Du fragst: "Hauptstadt von Frankreich?"
2. Jarvis sieht Korrektur im Context
3. Jarvis antwortet: "Paris" (richtig!)
```

## 🎯 Nächste Schritte

1. **Nutze Jarvis regelmäßig** und gib Feedback
2. **Korrigiere Fehler** wenn sie auftreten
3. **Beobachte Verbesserungen** im Lernen-Tab
4. **Experimentiere** mit verschiedenen Fragen

## 📖 Mehr Infos

Siehe `CONTINUOUS_LEARNING_README.md` für:
- Detaillierte Architektur
- API-Dokumentation
- Datenbank-Schema
- Troubleshooting
- Best Practices

**Viel Spaß beim Lernen!** 🚀
