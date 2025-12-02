# NeonMind - Deployment Guide

## Schnellstart mit Docker

### 1. Voraussetzungen
- Docker 20.10+
- Docker Compose 2.0+

### 2. Container starten

```bash
cd /home/ubuntu/NeonMind
docker-compose up -d
```

### 3. Datenbank initialisieren

```bash
docker-compose exec web python seed.py
```

### 4. Zugriff

- Anwendung: http://localhost:5000
- PostgreSQL: localhost:5432
- Redis: localhost:6379

### 5. Demo-Accounts

| Username | Password | Rolle |
|----------|----------|-------|
| admin    | admin123 | Admin |
| player1  | player123| User  |
| player2  | player123| User  |

## Lokale Entwicklung

### 1. Python Environment

```bash
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Datenbank Setup

```bash
sudo service postgresql start
sudo -u postgres createdb neonmind
```

### 3. Redis starten

```bash
sudo service redis-server start
```

### 4. Anwendung starten

```bash
python run.py
```

## Production

### SECRET_KEY generieren

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### Nginx Reverse Proxy

```nginx
server {
    listen 80;
    server_name neonmind.example.com;

    location / {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    location /socket.io {
        proxy_pass http://localhost:5000/socket.io;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## Wartung

### Logs

```bash
docker-compose logs -f web
```

### Backup

```bash
docker-compose exec db pg_dump -U neonmind neonmind > backup.sql
```

### Updates

```bash
git pull
docker-compose build
docker-compose up -d
```

