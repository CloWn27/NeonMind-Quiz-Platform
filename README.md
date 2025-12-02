# 🌆 NeonMind - Cyberpunk FiSi Quiz Platform

Eine interaktive Lernplattform für Systemadministratoren (FiSi) im Stil von Cyberpunk 2077. Kombiniert fachliche Tiefe (IHK Lernfelder) mit Kahoot-artigem Multiplayer-Spaß.

![NeonMind](https://img.shields.io/badge/Status-Production%20Ready-brightgreen)
![Python](https://img.shields.io/badge/Python-3.11-blue)
![Flask](https://img.shields.io/badge/Flask-3.0-lightgrey)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue)

## ✨ Features

### 🎮 Cyber-Warfare (Multiplayer)
- Kahoot-Style Multiplayer mit Host-View (Beamer) und Controller-View (Smartphone)
- Echtzeit-Synchronisation via SocketIO
- Wake Lock API (Display bleibt an)
- Reconnection-Support (F5-Reload unterstützt)
- Glitch-Effekte bei Fehlern
- Streak-Boni und "Jammer"-Hacks gegen Gegner

### 💀 Survival-Modus
- **Hardcore:** Falsche Antwort = Rauswurf
- **Normal:** Hoher Punktabzug
- Adaptive Schwierigkeitsgrade

### 🏠 The Safehouse (Dashboard)
- Radar-Chart zur Visualisierung der Kompetenz in allen Lernfeldern
- XP und Level-System
- Achievement-System
- Statistiken und Fortschritt

### 🤖 Ripperdoc (Avatar-Editor)
- Visueller Editor mit Layer-System
- Kopf, Cyberware, Farbe
- JSON-basierte Konfiguration

### 👁️ God-Mode (Admin)
- Laufende Spiele steuern
- User kicken
- Fragen annullieren
- Statistiken und Monitoring

## 🛠️ Tech Stack

- **Backend:** Flask 3.0 + Flask-SocketIO
- **Database:** PostgreSQL 15
- **Cache/Queue:** Redis 7
- **Frontend:** HTML5 (Jinja2) + Tailwind CSS + Vanilla JS
- **Charts:** Chart.js
- **Deployment:** Docker + Docker Compose
- **i18n:** Flask-Babel (DE/EN)

## 📦 Installation

### Voraussetzungen
- Docker & Docker Compose
- Python 3.11+ (für lokale Entwicklung)
- Git

### Mit Docker (Empfohlen)

1. **Repository klonen:**
```bash
git clone <repository-url>
cd NeonMind
```

2. **Umgebungsvariablen konfigurieren:**
```bash
cp .env.example .env
# Bearbeite .env und setze SECRET_KEY
```

3. **Container starten:**
```bash
docker-compose up -d
```

4. **Datenbank initialisieren und Daten importieren:**
```bash
docker-compose exec web python seed.py
```

5. **Anwendung öffnen:**
```
http://localhost:5000
```

### Lokale Entwicklung (ohne Docker)

1. **Virtual Environment erstellen:**
```bash
python3.11 -m venv venv
source venv/bin/activate  # Linux/Mac
# oder
venv\Scripts\activate  # Windows
```

2. **Dependencies installieren:**
```bash
pip install -r requirements.txt
```

3. **PostgreSQL und Redis starten:**
```bash
# PostgreSQL
sudo service postgresql start

# Redis
sudo service redis-server start
```

4. **Umgebungsvariablen setzen:**
```bash
cp .env.example .env
# Bearbeite .env mit lokalen Datenbank-Credentials
```

5. **Datenbank initialisieren:**
```bash
python seed.py
```

6. **Anwendung starten:**
```bash
python run.py
```

## 🎯 Verwendung

### Demo-Accounts

Nach dem Seeding sind folgende Test-Accounts verfügbar:

| Username | Password | Rolle |
|----------|----------|-------|
| admin | admin123 | Admin |
| player1 | player123 | User |
| player2 | player123 | User |

### Spielablauf

1. **Login** mit einem der Demo-Accounts
2. **Dashboard** öffnen ("The Safehouse")
3. **Neues Spiel erstellen** oder **Spiel beitreten**
4. **Host-View** (Beamer) und **Controller-View** (Smartphone) nutzen
5. **Fragen beantworten** und Punkte sammeln
6. **Achievements freischalten** und Level aufsteigen

## 📊 Datenbank-Schema

### Haupttabellen

- **users:** Benutzer mit XP, Level, Avatar-Config
- **lernfelder:** IHK Lernfelder (LF 1, LF 2, ...)
- **fragen:** Quiz-Fragen mit Metadaten
- **antworten:** Antwortoptionen
- **spiel_sitzungen:** Game Sessions
- **teilnahmen:** Spieler-Teilnahmen mit Scores
- **achievements:** Erfolge/Badges

## 🔧 Konfiguration

### Umgebungsvariablen (.env)

```bash
# Database
DATABASE_URL=postgresql://user:pass@host:5432/dbname

# Redis
REDIS_URL=redis://host:6379/0

# Flask
SECRET_KEY=your-secret-key
FLASK_ENV=production

# SocketIO
SOCKETIO_MESSAGE_QUEUE=redis://host:6379/0

# i18n
BABEL_DEFAULT_LOCALE=de
BABEL_DEFAULT_TIMEZONE=Europe/Berlin
```

### Game Settings (config.py)

```python
MAX_PLAYERS_PER_ROOM = 50
QUESTION_TIME_BUFFER = 2
STREAK_BONUS_MULTIPLIER = 1.5
```

## 🚀 Deployment

### Production Deployment

1. **SECRET_KEY generieren:**
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

2. **docker-compose.yml anpassen:**
```yaml
environment:
  SECRET_KEY: <generated-secret-key>
  FLASK_ENV: production
```

3. **Container starten:**
```bash
docker-compose up -d
```

4. **Logs überwachen:**
```bash
docker-compose logs -f web
```

### Reverse Proxy (Nginx)

```nginx
server {
    listen 80;
    server_name neonmind.example.com;

    location / {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /socket.io {
        proxy_pass http://localhost:5000/socket.io;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## 📝 API Endpoints

### REST API

- `GET /api/user/stats` - User-Statistiken für Radar-Chart
- `PUT /api/user/avatar` - Avatar-Konfiguration aktualisieren
- `GET /api/questions` - Fragen mit Filtern abrufen
- `GET /api/lernfelder` - Alle Lernfelder
- `GET /api/leaderboard` - Top-Spieler

### SocketIO Events

**Client → Server:**
- `join_game` - Spiel beitreten
- `start_game` - Spiel starten (Host)
- `submit_answer` - Antwort einreichen
- `next_question` - Nächste Frage (Host)
- `use_jammer` - Jammer-Hack einsetzen
- `reconnect_game` - Reconnect nach Disconnect

**Server → Client:**
- `connected` - Verbindung bestätigt
- `room_state` - Aktueller Raum-Status
- `new_question` - Neue Frage
- `answer_result` - Antwort-Ergebnis
- `game_finished` - Spiel beendet
- `jammer_attack` - Jammer-Angriff
- `kicked` - Aus Spiel entfernt

## 🧪 Testing

```bash
# Unit Tests
pytest

# Mit Coverage
pytest --cov=app tests/
```

## 🤝 Contributing

1. Fork das Repository
2. Feature Branch erstellen (`git checkout -b feature/AmazingFeature`)
3. Changes committen (`git commit -m 'Add AmazingFeature'`)
4. Branch pushen (`git push origin feature/AmazingFeature`)
5. Pull Request öffnen

## 📄 Lizenz

MIT License - siehe [LICENSE](LICENSE) für Details

## 👥 Credits

- **Design Inspiration:** Cyberpunk 2077
- **Game Concept:** Kahoot!
- **Quiz Data:** IHK Lernfelder für Fachinformatiker Systemintegration

## 🐛 Known Issues

- Wake Lock API funktioniert nur über HTTPS (außer localhost)
- Safari hat eingeschränkte SocketIO-Unterstützung
- Jammer-Hack benötigt Cooldown-System (TODO)

## 🗺️ Roadmap

- [ ] Mobile App (React Native)
- [ ] Voice Chat Integration
- [ ] Tournament-Modus
- [ ] Custom Quiz Creator
- [ ] AI-Powered Question Generation
- [ ] Blockchain-basierte Achievements (NFTs)

## 📞 Support

Bei Fragen oder Problemen:
- GitHub Issues: [Issues](https://github.com/yourusername/neonmind/issues)
- Email: support@neonmind.de

---

**Made with 💙 and ⚡ in the Cyberpunk Universe**
