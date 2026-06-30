# Android-App ↔ techkev-Appstore Backend

Dieses Dokument beschreibt, wie eine Android-App den techkev-Appstore über
dessen REST-API (`/api/v1/...`) ansteuert: Apps durchsuchen, Updates prüfen,
APKs herunterladen, installieren und das Tracking dafür melden.

Die vollständige, interaktive OpenAPI-Dokumentation steht zusätzlich unter
`http://<server>:<port>/docs` zur Verfügung.

## 1. Basis-Konfiguration

| Einstellung | Wert |
|---|---|
| Base-URL | `http://<server>:<PORT>` (das vom Admin konfigurierte Nginx-Frontend) |
| API-Präfix | `/api/v1` |
| Authentifizierung | Header `X-API-Key: <API_KEY>` bei **jedem** Request an `/api/v1/...` |

Der `API_KEY` wird vom Admin in der `.env` des Servers festgelegt und muss in
der Android-App fest hinterlegt oder bei der Ersteinrichtung eingegeben
werden. Ohne gültigen Header antwortet die API mit `401 Unauthorized`.

> **Hinweis:** Der API-Key wird im Klartext-Header übertragen. Für den
> Produktivbetrieb sollte der Appstore daher hinter HTTPS (z. B. über einen
> vorgelagerten Reverse Proxy mit TLS-Terminierung) betrieben werden.

Web-Interface-Login (`/login`, Session-Cookie) ist ausschließlich für den
Admin-Browser-Zugriff gedacht und wird von der Android-App **nicht**
verwendet.

## 2. Typischer Ablauf in der App

```
App-Start
  └─ GET /api/v1/apps            → Store-Liste anzeigen (Icons, Namen, Kategorien)
  └─ GET /api/v1/categories      → Kategorie-Filter im UI befüllen

Nutzer durchsucht / filtert
  └─ GET /api/v1/apps?search=...&category=...

Nutzer öffnet eine App
  └─ GET /api/v1/apps/{package_name}   → Details + vollständiger Versionsverlauf

Nutzer lädt APK herunter
  └─ APK von "download_url" laden (wird direkt von Nginx ausgeliefert)
  └─ POST /api/v1/apps/{package_name}/download-count   → Download-Zähler erhöhen

Android installiert die APK (PackageInstaller / Session-API)
  └─ Bei Erfolg: POST /api/v1/apps/{package_name}/install-count → Installations-Zähler erhöhen

Periodischer Update-Check (z. B. beim App-Start oder per WorkManager)
  └─ Für jede installierte, vom Appstore stammende App:
     POST /api/v1/apps/check-update {"package_name": "...", "version_code": <installierte versionCode>}
  └─ Bei update_available=true: Download-URL aus der Antwort verwenden
```

## 3. Endpunkte im Detail

Alle Pfade sind relativ zur Base-URL und benötigen den Header `X-API-Key`.

### `GET /api/v1/apps`

Listet alle aktiven Apps mit ihrer jeweils neuesten Version.

Query-Parameter (alle optional):

| Parameter | Typ | Beschreibung |
|---|---|---|
| `search` | string | Volltextsuche über Anzeigename und Package-Name |
| `category` | string | exakter Kategorie-Filter |
| `skip` | int | Pagination-Offset (Default `0`) |
| `limit` | int | Max. Anzahl Ergebnisse (Default `50`) |

Antwort:

```json
{
  "total": 2,
  "apps": [
    {
      "id": 1,
      "package_name": "de.example.app",
      "display_name": "Beispiel-App",
      "category": "Tools",
      "description": "Kurzbeschreibung",
      "is_active": true,
      "icon_url": "/data/icons/de.example.app.png",
      "created_at": "2026-05-01T10:00:00",
      "updated_at": "2026-06-20T08:30:00",
      "latest_version": {
        "id": 5,
        "version_name": "1.4.0",
        "version_code": 14,
        "changelog": "Bugfixes",
        "apk_size_bytes": 18345213,
        "min_sdk": 24,
        "target_sdk": 34,
        "download_count": 12,
        "install_count": 9,
        "uploaded_at": "2026-06-20T08:30:00",
        "download_url": "/data/apks/3f9a....apk"
      },
      "versions": []
    }
  ]
}
```

`icon_url` und `download_url` sind relative Pfade auf demselben Server (von
Nginx ausgeliefert) und müssen von der App mit der Base-URL zusammengesetzt
werden, z. B. `https://appstore.example.com` + `download_url`.

### `GET /api/v1/apps/{package_name}`

Liefert die Details **einer** App inkl. vollständigem `versions`-Array
(Versionsverlauf, neueste zuerst), je Eintrag mit eigenem `changelog`.
`404`, falls die App nicht existiert oder deaktiviert ist.

### `GET /api/v1/apps/{package_name}/versions`

Liefert ausschließlich den Versionsverlauf (Liste von `AppVersion`-Objekten)
einer App – praktisch für eine reine Changelog-Ansicht.

### `GET /api/v1/categories`

```json
{ "categories": ["Tools", "Spiele", "Produktivität"] }
```

Kategorien sind Freitext (vom Admin beim Upload vergeben); diese Liste enthält
alle aktuell verwendeten Werte für Filter-UI.

### `POST /api/v1/apps/check-update`

Request:

```json
{ "package_name": "de.example.app", "version_code": 12 }
```

Response, falls ein Update verfügbar ist:

```json
{
  "package_name": "de.example.app",
  "update_available": true,
  "latest_version_name": "1.4.0",
  "latest_version_code": 14,
  "changelog": "Bugfixes",
  "download_url": "/data/apks/3f9a....apk",
  "apk_size_bytes": 18345213
}
```

Ist keine neuere Version vorhanden (oder die App unbekannt/deaktiviert),
liefert die Antwort `"update_available": false` und alle übrigen Felder als
`null`.

### `POST /api/v1/apps/{package_name}/download-count`

Vom Client nach einem erfolgreichen APK-Download aufzurufen, um den
Download-Zähler zu erhöhen. Optionaler Body, falls nicht die neueste Version
gemeint ist:

```json
{ "version_code": 14 }
```

Ohne Body (oder `version_code: null`) wird die jeweils neueste Version
gezählt.

### `POST /api/v1/apps/{package_name}/install-count`

Analog zu `download-count`, aber für das **Installations-Tracking**: von der
Android-App aufzurufen, nachdem die APK erfolgreich installiert wurde (z. B.
nach positivem Callback des `PackageInstaller`). Gleicher optionaler
`version_code`-Body wie oben.

> Download- und Installationszählung erfolgen ausschließlich durch explizite
> Aufrufe der Android-App – es gibt kein automatisches Tracking über Nginx.

## 4. Fehlerfälle

| Status | Bedeutung |
|---|---|
| `401` | API-Key fehlt oder ist ungültig |
| `404` | App / Version nicht gefunden oder deaktiviert |
| `422` | Request-Body entspricht nicht dem erwarteten Schema |

## 5. Hinweise zur Versionsverwaltung

- Pro App (`package_name`) können mehrere Versionen parallel im Store liegen;
  ältere Versionen bleiben über ihre eigene `download_url` abrufbar.
- `latest_version` in der App-Liste ist immer die Version mit dem höchsten
  `version_code`.
- Jede Version hat ihr eigenes `changelog`-Feld – die App kann daraus z. B.
  eine "Was ist neu"-Ansicht über mehrere Versionen hinweg zusammenstellen
  (`GET /api/v1/apps/{package_name}/versions`).
