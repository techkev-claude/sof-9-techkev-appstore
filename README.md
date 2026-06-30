# techkev-Appstore

Selbst gehostete Web-Applikation zum Verwalten und Bereitstellen von APK-Dateien.
Über ein Web-Interface (mit Login) können APKs hochgeladen, kategorisiert und
versioniert werden. Eine REST-API (`/api/v1/...`, abgesichert per API-Key)
stellt alle Endpunkte bereit, die eine Android-App zum Durchsuchen,
Herunterladen und automatischen Aktualisieren von Apps benötigt.

Details zur Anbindung der Android-App: [docs/ANDROID_INTEGRATION.md](docs/ANDROID_INTEGRATION.md)

## Features

- Web-Interface mit Login-Seite (Session-Cookie) zum Hochladen, Kategorisieren
  und Löschen von APKs
- Automatische Extraktion von Package-Name, Versionsinfos und App-Icon beim Upload
- Versionsverwaltung: mehrere Versionen pro App bleiben parallel verfügbar,
  inkl. Changelog je Version
- REST-API für eine Android-App: App-Liste, Suche, Kategorie-Filter,
  Update-Check, Download-/Installations-Tracking
- APK-Auslieferung direkt über Nginx (kein Umweg über FastAPI)

## Setup über Portainer

1. **Repository klonen / in Portainer hinterlegen**

   ```
   git clone <repo-url>
   ```

2. **`.env` anlegen**

   ```
   cp .env.example .env
   ```

   Anschließend alle Werte in `.env` setzen, insbesondere:
   - `ADMIN_USER` / `ADMIN_PASSWORD` – Zugangsdaten für das Web-Interface
   - `API_KEY` – wird von der Android-App im Header `X-API-Key` mitgeschickt
   - `SECRET_KEY` – zufälliger, geheimer Wert zum Signieren der Session-Cookies
   - `DATA_PATH` – Host-Verzeichnis, in dem APKs, Icons und die SQLite-DB
     persistent abgelegt werden

   **Wichtig:** `SECRET_KEY`, `ADMIN_PASSWORD` und `API_KEY` müssen für den
   Produktivbetrieb zwingend auf eigene, geheime Werte geändert werden.

3. **In Portainer:** Stacks → Add Stack → Repository-URL eintragen (oder den
   Inhalt von `docker-compose.yml` direkt als Web-Editor-Stack einfügen) und
   die Variablen aus `.env` als Umgebungsvariablen des Stacks hinterlegen.

4. **Stack deployen.**

5. **Aufruf** unter `http://<server>:<PORT>` (Standard-Port: `8084`).
   Beim ersten Aufruf erscheint die Login-Seite; anmelden mit `ADMIN_USER` /
   `ADMIN_PASSWORD`.

   Die interaktive API-Dokumentation ist unter `http://<server>:<PORT>/docs`
   erreichbar (Endpunkte unter `/api/v1` benötigen dort den Header
   `X-API-Key`, um getestet werden zu können).

## Lokale Entwicklung ohne Docker

```bash
cd backend
pip install -r requirements.txt
export ADMIN_USER=admin ADMIN_PASSWORD=changeme API_KEY=devkey SECRET_KEY=devsecret
export DB_PATH=./dev.sqlite3 APK_STORAGE_PATH=./data/apks ICON_STORAGE_PATH=./data/icons
mkdir -p ./data/apks ./data/icons
uvicorn main:app --reload
```

Da Nginx im lokalen Modus fehlt, werden APKs/Icons dann direkt über
`/data/apks/...` bzw. `/data/icons/...` aus dem Backend nicht automatisch
ausgeliefert – dafür im Container-Setup über Nginx (siehe `nginx/nginx.conf`).

## Konfiguration

| Variable | Beschreibung | Pflicht |
|---|---|---|
| `ADMIN_USER` | Benutzername für die Web-Interface Login-Seite | ✅ |
| `ADMIN_PASSWORD` | Passwort für die Web-Interface Login-Seite | ✅ |
| `API_KEY` | API-Key, den die Android-App im Header `X-API-Key` mitschickt | ✅ |
| `SECRET_KEY` | Secret zum Signieren der Session-Cookies | ✅ |
| `DB_PATH` | Pfad zur SQLite-Datei im Container | ✅ |
| `PORT` | Externer Port für Nginx | ✅ |
| `DATA_PATH` | Host-Pfad für persistente Daten (APKs, Icons, DB) | ✅ |
| `APK_MAX_SIZE_MB` | Maximale APK-Dateigröße in MB | optional (Default 500) |
