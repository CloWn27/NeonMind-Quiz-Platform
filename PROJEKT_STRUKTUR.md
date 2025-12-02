# NeonMind - Vollständige Projektstruktur

## Verzeichnisstruktur

NeonMind/
├── app/                          # Hauptanwendung
│   ├── models/                   # SQLAlchemy Datenbankmodelle
│   ├── routes/                   # Flask Blueprints
│   ├── services/                 # Business Logic
│   ├── templates/                # Jinja2 HTML Templates
│   ├── static/                   # CSS, JS, Assets
│   ├── __init__.py              # Flask App Factory
│   └── extensions.py            # Extensions
├── data/                         # Quiz JSON Daten
├── config.py                     # Konfiguration
├── run.py                        # Einstiegspunkt
├── seed.py                       # Datenbank Seeding
├── requirements.txt              # Dependencies
├── Dockerfile                    # Docker Image
├── docker-compose.yml            # Docker Compose
└── README.md                     # Dokumentation

## Hauptkomponenten

- Flask 3.0 + SocketIO für Realtime
- PostgreSQL 15 für Datenbank
- Redis 7 für Caching & Message Queue
- Tailwind CSS für Cyberpunk Design
- Chart.js für Radar Charts
- Docker für Deployment

