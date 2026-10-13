# Mitarbeiter-Hub

> *A small Flask prototype that bundles everyday team workflows (recurring to-dos, idea pool, tool tiles) for multiple locations in one web app.*

Der Mitarbeiter-Hub ist eine kleine Web-App, die Arbeitsabläufe für Teams an mehreren Standorten bündelt: Jeder Standort bekommt eine eigene Startseite mit Tool-Kacheln, eigenen Farben und eigener To-Do-Liste.

**Hinweis:** Das ist ein Prototyp (Proof of Concept), der nicht für den Produktivbetrieb gedacht ist. Was dafür noch fehlt, steht [weiter unten](#was-für-den-produktivbetrieb-noch-fehlt).

Dieses Repository ist eine bereinigte, generische Version eines Projekts, das ich an anderer Stelle für den echten Einsatz entwickelt und deployt habe, dort mit den tatsächlich benötigten Tools. Es zeigt Aufbau und Arbeitsweise, nicht den vollen Funktionsumfang des Originals.

**Was hier funktioniert und was nur Platzhalter ist:**

| Tool | Status in diesem Repo |
|---|---|
| Standort-Auswahl und Theming | funktioniert |
| To-Do-Liste (täglich/wöchentlich) | funktioniert |
| Ideenpool | in Arbeit (siehe [Bekannte Einschränkungen](#bekannte-einschränkungen)) |
| Rechnungs-Generator | **nur Demo-Kachel**, keine Logik (im Original: CSV zu PDF) |
| Dashboard, Schichtplaner, Trend-Tracker | **nur Demo-Kacheln**, keine Logik |

## Features

- **Standort-Auswahl:** Startseite mit allen Standorten, danach eine Kachel-Übersicht pro Standort
- **Multi-Standort-Theming:** Primär- und Sekundärfarbe sowie Icon pro Standort, gesteuert über `data/stores_config.json`
- **Team-To-Dos:**
  - Wochen-To-Dos, die jeden Montag zurückgesetzt werden
  - Tages-To-Dos, entweder *wiederkehrend* (täglicher Reset) oder *einmalig* mit Erledigungsdatum
  - Wochentag-Ansicht (Mo–Sa) mit Markierung für heute, überfällig und zukünftig
  - Anlegen, Bearbeiten, Abhaken und Löschen
- **Ideenpool:** Ideen und Verbesserungsvorschläge sammeln (gespeichert in `data/ideas.json`)
- **Demo-Kacheln:** Rechnungs-Generator, Dashboard, Schichtplaner und Trend-Tracker sind reine Platzhalter ohne Funktion. Ein Klick bewirkt nichts. Sie zeigen, wie weitere Tools in die Oberfläche eingebunden würden.

## Tech-Stack

- **Backend:** Python 3.12, Flask, Flask-SQLAlchemy, SQLite
- **Frontend:** Jinja2, Bootstrap 5, Font Awesome
- **Deployment:** Docker, Gunicorn

## Architektur in Kürze

- **Template-Vererbung:** Alle Seiten erben von `templates/base.html` (Navbar, Footer, Zurück-Button). Wiederkehrende Bausteine wie To-Do-Karte und Bearbeiten-Dialog liegen als Partials (`_todo_card.html`, `_todo_edit_modal.html`) vor und werden per `include` eingebunden.
- **Theming über CSS-Variablen:** `base.html` setzt `--primary-color` und `--secondary-color` aus der Standort-Konfiguration. Das gesamte Stylesheet nutzt nur diese Variablen, deshalb braucht ein neuer Standort kein zusätzliches CSS.
- **Lazy Reset der To-Dos:** Es gibt keinen Cronjob. Beim Aufruf der To-Do-Seite prüft die App, ob ein wiederkehrendes To-Do aus einem früheren Tag bzw. einer früheren Woche stammt, und setzt es dann zurück. Das ist einfach und robust, solange die Seite regelmäßig aufgerufen wird.
- **SQLite vs. JSON:** Die To-Dos werden oft gelesen und geändert und lassen sich nach Standort, Typ und Datum filtern, deshalb liegen sie in SQLite (über SQLAlchemy). Standort-Konfiguration und Ideenpool sind klein, ändern sich selten und sollen von Hand editierbar sein, deshalb sind sie JSON-Dateien.

## Lokal starten

```bash
pip install -r requirements.txt
python app.py
```

Die App läuft dann unter http://localhost:5000. Beim ersten Start wird automatisch eine leere Datenbank unter `instance/mitarbeiter_hub.db` angelegt.

## Docker

```bash
docker build -t mitarbeiter-hub:latest .
docker run -d \
  -p 5000:5000 \
  -v /pfad/zu/instance:/app/instance \
  -v /pfad/zu/data:/app/data \
  mitarbeiter-hub:latest
```

`instance/` (Datenbank) und `data/` (Konfiguration, Ideenpool) sollten als Volumes gemountet werden, sonst gehen die Daten beim Neubau des Containers verloren.

## Konfiguration

Die Standorte werden in `data/stores_config.json` gepflegt. Der Schlüssel (`"0"`, `"1"`, …) ist die Standort-ID in der URL (`/service/<id>`).

| Feld | Bedeutung |
|---|---|
| `name` | Anzeigename auf der Startseite |
| `short_name` | Kürzel, wird als Überschrift `<Kürzel>-Hub` angezeigt |
| `icon` | Font-Awesome-Klasse, z. B. `fa-store` |
| `services` | IDs der Kacheln, die an diesem Standort angezeigt werden (`todos`, `ideas`, `invoice`, `dashboard`, `schichtplan`, `trend-tracker`) |
| `primary_color` | Hauptfarbe (Buttons, Icons, Akzente) |
| `secondary_color` | Zweitfarbe (Hover-Zustände) |

Die verfügbaren Kacheln sind zentral in `SERVICES` in `app.py` definiert.

## Bekannte Einschränkungen

- **Ideenpool:** Die Routen `/service/<id>/ideas` fehlen aktuell in `app.py`, die Kachel führt deshalb zu einem 404. Das wird in einem separaten Commit behoben.

## Was für den Produktivbetrieb noch fehlt

- **HTTPS:** Reverse Proxy wie nginx oder Caddy mit Let's Encrypt, alternativ Tailscale-Zertifikate
- **Authentifizierung:** Login mit einem Zwei-Zonen-Modell: offene Team-Tools (To-Dos, Ideen) und geschützte Bereiche (z. B. Rechnungen, Auswertungen)
- **Netzwerkzugriff:** Zugriff nur über VPN mit Zugriffsregeln (z. B. Tailscale-ACLs)
- **CSRF-Schutz und Eingabevalidierung:** z. B. über Flask-WTF, dazu serverseitige Längen- und Formatprüfungen
- **CI/CD:** z. B. GitHub Actions für Build, Push des Images und Deploy
- **DB-Migrationen:** Flask-Migrate/Alembic statt der aktuellen Ad-hoc-Migration in `app.py`
- **Betrieb:** Backups von Datenbank und `data/`, Secrets über `.env`, Logging und Monitoring, automatisierte Tests

## Mögliche Erweiterungen

- **Monatsübersicht verkaufter Produkte:** Verkaufszahlen pro Standort und Monat, z. B. über die API eines Online-Shops
- **Schichtplan / Zeiterfassung:** Schichten planen und einsehen, Arbeitszeiten direkt im Hub erfassen
- **Bug- und Feedback-Kanal:** Fehler und Wünsche zur App strukturiert sammeln und nachverfolgen
- **Bestell- und Nachfrage-Tracking:** Kundenbestellungen erfassen und auswerten, um die Nachfrage besser einzuschätzen

## Lizenz

MIT-Lizenz, siehe [LICENSE](LICENSE).
