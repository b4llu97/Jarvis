# Kontinuierliches Lernen - Dokumentation

## Übersicht

Das **Kontinuierliche Lernen** Feature ermöglicht es Jarvis, aus Benutzer-Feedback und Korrekturen zu lernen und seine Antworten kontinuierlich zu verbessern.

---

## 🎯 Hauptfunktionen

### 1. **Benutzer-Feedback**
- ✅ Thumbs Up/Down Buttons nach jeder Antwort
- ✅ Optional: Kommentar bei negativem Feedback
- ✅ Automatische Speicherung mit Metadaten (Modell, Provider)

### 2. **Korrekturen**
- ✅ Benutzer kann falsche Antworten korrigieren
- ✅ Korrektur wird gespeichert und bei zukünftigen Anfragen berücksichtigt
- ✅ Dialog zeigt alte und neue Antwort

### 3. **Learning Context**
- ✅ Automatische Integration von Korrekturen in System-Prompt
- ✅ Negative Feedbacks werden berücksichtigt
- ✅ Dynamische Anpassung basierend auf Feedback-Historie

### 4. **Lern-Dashboard**
- ✅ Statistiken über Feedback und Bewertungen
- ✅ Bewertungsverteilung visualisiert
- ✅ Anzahl der Korrekturen
- ✅ Aktivität der letzten 7 Tage

---

## 🏗️ Architektur

```
┌─────────────────┐
│    Frontend     │
│  (React + TS)   │
└────────┬────────┘
         │
         │ Feedback/Corrections
         v
┌─────────────────┐
│   Toolserver    │
│  (FastAPI)      │
└────────┬────────┘
         │
         v
┌─────────────────┐
│  Feedback DB    │
│   (SQLite)      │
└─────────────────┘
         │
         │ Learning Context
         v
┌─────────────────┐
│  Orchestrator   │
│  (LLM Prompt)   │
└─────────────────┘
```

### Datenfluss

1. **Feedback geben:**
   - User klickt Thumbs Up/Down
   - Frontend sendet Feedback an Toolserver
   - Toolserver speichert in Feedback-DB

2. **Korrektur eingeben:**
   - User öffnet Korrektur-Dialog
   - Gibt richtige Antwort ein
   - Frontend sendet an Toolserver
   - Toolserver speichert in Corrections-Tabelle

3. **Lernen anwenden:**
   - Bei neuer Anfrage holt Orchestrator Learning Context
   - Toolserver liefert letzte 5 Korrekturen + negative Feedbacks
   - Orchestrator integriert in System-Prompt
   - LLM berücksichtigt bei Antwort

---

## 📁 Neue Dateien

### Backend

#### `services/toolserver/app/feedback_db.py`
Datenbank-Modul für Feedback und Korrekturen:
- `FeedbackDB` Klasse mit allen CRUD-Operationen
- 4 Tabellen: `feedback`, `corrections`, `learned_patterns`, `user_preferences`
- Methoden für Statistiken und Learning Context

**Wichtige Methoden:**
- `add_feedback()` - Feedback speichern
- `add_correction()` - Korrektur speichern
- `get_learning_context()` - Context für Prompt abrufen
- `get_statistics()` - Statistiken für Dashboard

#### `services/toolserver/app/main.py` (erweitert)
Neue API-Endpunkte:
- `POST /v1/feedback` - Feedback speichern
- `POST /v1/corrections` - Korrektur speichern
- `GET /v1/learning/context` - Learning Context abrufen
- `GET /v1/learning/statistics` - Statistiken abrufen
- `GET /v1/feedback/negative` - Negative Feedbacks
- `GET /v1/corrections` - Alle Korrekturen
- `POST /v1/preferences` - Präferenz setzen
- `GET /v1/preferences/{key}` - Präferenz abrufen

#### `services/orchestrator/app/logic.py` (erweitert)
- Neue Funktion `get_learning_context()`
- Integration in `process_query()`
- Learning Context wird automatisch in System-Prompt eingefügt

### Frontend

#### `services/frontend/src/components/FeedbackButtons.tsx`
Feedback-Komponente mit:
- Thumbs Up/Down Buttons
- Kommentar-Dialog bei negativem Feedback
- Korrektur-Dialog mit Vergleich
- Toast-Benachrichtigungen

#### `services/frontend/src/components/LearningDashboard.tsx`
Dashboard-Komponente mit:
- 4 Statistik-Karten (Total, Average, Corrections, Recent)
- Bewertungsverteilung als Balkendiagramm
- Info-Box über Lern-Mechanismus

#### `services/frontend/src/services/api.ts` (erweitert)
Neue API-Funktionen:
- `submitFeedback()` - Feedback senden
- `submitCorrection()` - Korrektur senden
- `getLearningStatistics()` - Statistiken laden

#### `services/frontend/src/App.tsx` (erweitert)
- Integration von `FeedbackButtons` nach jeder Assistant-Nachricht
- Neuer "Lernen" Tab mit `LearningDashboard`
- Metadaten (model, provider, query) in Messages

---

## 🚀 Installation

### 1. Backend aktualisieren

Die neuen Dateien sind bereits erstellt. Starte die Services neu:

```bash
cd /home/ubuntu/Jarvis

# Toolserver neu bauen (neue Dependencies)
docker-compose build toolserver orchestrator

# Services neu starten
docker-compose up -d
```

### 2. Frontend aktualisieren

```bash
# Frontend neu bauen
docker-compose build frontend

# Service neu starten
docker-compose restart frontend
```

### 3. Testen

```bash
# Toolserver Health Check
curl http://localhost:8002/health

# Learning Statistics abrufen
curl http://localhost:8002/v1/learning/statistics
```

---

## 💡 Verwendung

### Als Benutzer

#### Feedback geben

1. Chatte mit Jarvis
2. Nach jeder Antwort erscheinen 3 Buttons:
   - 👍 **Hilfreich** - Positive Bewertung
   - 👎 **Nicht hilfreich** - Negative Bewertung (mit optionalem Kommentar)
   - 💬 **Korrigieren** - Richtige Antwort eingeben

3. Klicke auf den entsprechenden Button
4. Bei negativem Feedback oder Korrektur öffnet sich ein Dialog
5. Feedback wird gespeichert und Jarvis lernt daraus

#### Statistiken ansehen

1. Klicke auf den **"Lernen"** Tab
2. Sieh dir die Statistiken an:
   - Wie viele Feedbacks wurden gegeben?
   - Wie ist die durchschnittliche Bewertung?
   - Wie viele Korrekturen gab es?
   - Bewertungsverteilung

### Als Entwickler

#### Feedback-Datenbank zugreifen

```python
from feedback_db import FeedbackDB

db = FeedbackDB("/app/data/feedback.db")

# Statistiken abrufen
stats = db.get_statistics()
print(f"Average Rating: {stats['average_rating']}")

# Learning Context abrufen
context = db.get_learning_context("", limit=5)
print(context)

# Negative Feedbacks
negative = db.get_negative_feedback(limit=10)
for fb in negative:
    print(f"Query: {fb['query']}")
    print(f"Rating: {fb['rating']}")
    print(f"Comment: {fb['comment']}")
```

#### API-Endpunkte nutzen

```bash
# Feedback hinzufügen
curl -X POST http://localhost:8002/v1/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Was ist 2+2?",
    "response": "4",
    "rating": 5,
    "model": "gpt-4.1-mini",
    "provider": "openai"
  }'

# Korrektur hinzufügen
curl -X POST http://localhost:8002/v1/corrections \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Hauptstadt von Frankreich?",
    "wrong_response": "London",
    "correct_response": "Paris"
  }'

# Statistiken abrufen
curl http://localhost:8002/v1/learning/statistics

# Learning Context abrufen
curl http://localhost:8002/v1/learning/context?limit=5
```

---

## 🔧 Konfiguration

### Umgebungsvariablen

In `docker-compose.yml` oder `config/.env`:

```bash
# Feedback-Datenbank Pfad
FEEDBACK_DB_PATH=/app/data/feedback.db
```

### Learning Context Limit

Im Orchestrator wird standardmäßig die letzten 5 Korrekturen/Feedbacks abgerufen. 
Dies kann in `services/orchestrator/app/logic.py` angepasst werden:

```python
def get_learning_context() -> str:
    response = requests.get(f"{TOOLSERVER_URL}/v1/learning/context?limit=10", timeout=5)
    # Ändere limit=10 auf gewünschten Wert
```

---

## 📊 Datenbank-Schema

### Tabelle: `feedback`

| Spalte | Typ | Beschreibung |
|--------|-----|--------------|
| id | INTEGER | Primary Key |
| query | TEXT | Benutzer-Anfrage |
| response | TEXT | Assistant-Antwort |
| rating | INTEGER | 1-5 Bewertung |
| comment | TEXT | Optional: Kommentar |
| model | TEXT | LLM-Modell |
| provider | TEXT | LLM-Provider |
| timestamp | DATETIME | Zeitstempel |

### Tabelle: `corrections`

| Spalte | Typ | Beschreibung |
|--------|-----|--------------|
| id | INTEGER | Primary Key |
| query | TEXT | Original-Anfrage |
| wrong_response | TEXT | Falsche Antwort |
| correct_response | TEXT | Richtige Antwort |
| context | TEXT | Zusätzlicher Kontext |
| timestamp | DATETIME | Zeitstempel |

### Tabelle: `learned_patterns`

| Spalte | Typ | Beschreibung |
|--------|-----|--------------|
| id | INTEGER | Primary Key |
| pattern_type | TEXT | Art des Patterns |
| query_pattern | TEXT | Anfrage-Muster |
| response_pattern | TEXT | Antwort-Muster |
| confidence | REAL | Konfidenz (0-1) |
| usage_count | INTEGER | Verwendungszähler |
| last_used | DATETIME | Letzte Verwendung |
| created_at | DATETIME | Erstellungszeitpunkt |

### Tabelle: `user_preferences`

| Spalte | Typ | Beschreibung |
|--------|-----|--------------|
| id | INTEGER | Primary Key |
| preference_key | TEXT | Präferenz-Schlüssel |
| preference_value | TEXT | Präferenz-Wert |
| updated_at | DATETIME | Letztes Update |

---

## 🎓 Wie funktioniert das Lernen?

### 1. Feedback-Sammlung

- Benutzer gibt Feedback (1-5 Sterne)
- Feedback wird mit Metadaten gespeichert
- Negative Feedbacks (1-2 Sterne) werden besonders markiert

### 2. Korrektur-Speicherung

- Benutzer korrigiert falsche Antwort
- Alte und neue Antwort werden gespeichert
- Kontext kann hinzugefügt werden

### 3. Learning Context Generierung

Bei jeder neuen Anfrage:
1. Orchestrator ruft Learning Context ab
2. Toolserver liefert:
   - Letzte 5 Korrekturen
   - Letzte 5 negative Feedbacks mit Kommentaren
3. Context wird formatiert als Markdown

### 4. Prompt-Integration

Learning Context wird in System-Prompt eingefügt:

```
[System Prompt]
[Persona Prompt]
[Tools Description]

## Frühere Korrekturen (lerne daraus):

1. Frage: Was ist die Hauptstadt von Frankreich?
   Falsche Antwort: London
   Richtige Antwort: Paris

2. Frage: Wie viele Kontinente gibt es?
   Falsche Antwort: 6
   Richtige Antwort: 7

## Negatives Feedback (vermeide solche Antworten):

1. Frage: Erkläre Quantenphysik
   Problematische Antwort: Das ist zu kompliziert...
   Feedback: Zu oberflächlich, mehr Details gewünscht

Bitte berücksichtige diese früheren Korrekturen und Feedback bei deiner Antwort.
```

### 5. LLM-Verarbeitung

- LLM erhält erweiterten Prompt
- Berücksichtigt Korrekturen bei Antwort
- Vermeidet wiederholte Fehler

---

## 📈 Best Practices

### Für Benutzer

1. **Gib regelmäßig Feedback**
   - Auch positive Bewertungen helfen!
   - Kommentare bei negativem Feedback sind wertvoll

2. **Korrigiere präzise**
   - Gib die vollständige richtige Antwort
   - Füge Kontext hinzu wenn nötig

3. **Sei konsistent**
   - Ähnliche Fehler ähnlich korrigieren
   - Klare, eindeutige Korrekturen

### Für Entwickler

1. **Monitoring**
   - Überwache Feedback-Statistiken
   - Analysiere negative Feedbacks
   - Identifiziere Muster

2. **Datenbank-Wartung**
   - Backup der Feedback-DB
   - Periodisches Cleanup alter Einträge
   - Index-Optimierung bei vielen Einträgen

3. **Prompt-Optimierung**
   - Teste verschiedene Context-Limits
   - Experimentiere mit Formatierung
   - A/B-Testing verschiedener Ansätze

---

## 🔍 Troubleshooting

### Feedback wird nicht gespeichert

```bash
# Prüfe Toolserver Logs
docker-compose logs toolserver | grep feedback

# Prüfe Datenbank
docker-compose exec toolserver ls -la /app/data/feedback.db

# Teste API direkt
curl -X POST http://localhost:8002/v1/feedback \
  -H "Content-Type: application/json" \
  -d '{"query":"test","response":"test","rating":5}'
```

### Learning Context wird nicht geladen

```bash
# Prüfe Orchestrator Logs
docker-compose logs orchestrator | grep "learning"

# Teste Context-Endpunkt
curl http://localhost:8002/v1/learning/context

# Prüfe Netzwerk-Verbindung
docker-compose exec orchestrator curl http://toolserver:8002/health
```

### Frontend zeigt keine Feedback-Buttons

```bash
# Prüfe Browser-Konsole für Fehler
# Prüfe ob FeedbackButtons-Komponente importiert ist
docker-compose logs frontend

# Rebuild Frontend
docker-compose build frontend
docker-compose restart frontend
```

### Statistiken sind leer

```bash
# Prüfe ob Datenbank initialisiert ist
docker-compose exec toolserver python3 -c "
from feedback_db import FeedbackDB
db = FeedbackDB('/app/data/feedback.db')
print(db.get_statistics())
"

# Füge Test-Daten hinzu
curl -X POST http://localhost:8002/v1/feedback \
  -H "Content-Type: application/json" \
  -d '{"query":"Test","response":"Test","rating":5}'
```

---

## 🚀 Nächste Schritte

### Kurzfristig

1. **Testen**
   - Feedback geben und Statistiken prüfen
   - Korrekturen eingeben und Wirkung beobachten
   - Dashboard erkunden

2. **Feedback sammeln**
   - Nutze Jarvis regelmäßig
   - Gib ehrliches Feedback
   - Korrigiere Fehler

### Mittelfristig

3. **Pattern Learning**
   - Automatische Extraktion von Patterns aus Korrekturen
   - Machine Learning für Pattern-Erkennung
   - Confidence-Scoring

4. **Advanced Analytics**
   - Zeitreihen-Analyse der Bewertungen
   - Korrelation zwischen Feedback und Modell
   - A/B-Testing verschiedener Prompts

5. **User Preferences**
   - Lernstil-Präferenzen
   - Antwort-Länge Präferenzen
   - Ton und Stil Präferenzen

### Langfristig

6. **Fine-Tuning**
   - Sammle genug Daten für Fine-Tuning
   - Trainiere eigenes Modell auf Korrekturen
   - Evaluiere Performance

7. **Reinforcement Learning**
   - RLHF (Reinforcement Learning from Human Feedback)
   - Automatische Belohnung basierend auf Feedback
   - Kontinuierliche Verbesserung

8. **Multi-User Learning**
   - Lernen über mehrere Benutzer hinweg
   - Personalisiertes Lernen pro Benutzer
   - Federated Learning

---

## 📚 Referenzen

- [RLHF Paper](https://arxiv.org/abs/2203.02155)
- [Feedback-Driven Learning](https://arxiv.org/abs/2204.05862)
- [Human-in-the-Loop ML](https://www.manning.com/books/human-in-the-loop-machine-learning)

---

**Viel Erfolg mit dem Kontinuierlichen Lernen!** 🎓🚀
