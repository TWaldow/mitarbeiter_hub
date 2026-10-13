import os
import json
from datetime import date, timedelta, datetime
from flask import Flask, render_template, request, redirect, url_for
from sqlalchemy import inspect, text
from models import db, Todo

WOCHENTAGE_DE = ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag', 'Sonntag']

app = Flask(__name__)

basedir = os.path.abspath(os.path.dirname(__file__))
os.makedirs(os.path.join(basedir, 'instance'), exist_ok=True)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'instance', 'mitarbeiter_hub.db')
db.init_app(app)

def migriere_todo_tabelle():
    """Einmalige Migration: alte Spalte 'typ' umbenennen, neue Spalten hinzufügen,
    bestehende Daten migrieren. Läuft nur, wenn die Migration noch nicht durchgeführt wurde."""
    
    inspector = inspect(db.engine)
    spalten = [col['name'] for col in inspector.get_columns('todos')]
    
    # Prüfen ob Migration schon gelaufen ist (anhand der neuen Spalte 'art')
    if 'art' in spalten:
        return  # Migration bereits durchgeführt, nichts zu tun
    
    with db.engine.connect() as conn:
        # 1. Neue Spalten hinzufügen
        conn.execute(text("ALTER TABLE todos ADD COLUMN art VARCHAR(15)"))
        conn.execute(text("ALTER TABLE todos ADD COLUMN erledigungsdatum DATE"))
        
        # 2. Spalte umbenennen (datum -> erstellungsdatum)
        if 'datum' in spalten and 'erstellungsdatum' not in spalten:
            conn.execute(text("ALTER TABLE todos RENAME COLUMN datum TO erstellungsdatum"))
        
        # 3. Bestehende typ-Werte umbenennen
        conn.execute(text("UPDATE todos SET typ = 'tagestodo' WHERE typ = 'daily'"))
        conn.execute(text("UPDATE todos SET typ = 'wochentodo' WHERE typ = 'weekly'"))
        
        # 4. art für bestehende Tages-Todos befüllen
        conn.execute(text("UPDATE todos SET art = 'wiederkehrend' WHERE typ = 'tagestodo'"))
        
        conn.commit()
    
    print("Todo-Tabelle erfolgreich migriert.")

with app.app_context():
    db.create_all()
    migriere_todo_tabelle()

# ZENTRALE LISTE ALLER SERVICES
# 'demo': True = Beispiel-Kachel ohne hinterlegte Logik (Klick führt nirgendwohin)
SERVICES = [
    {
        'id': 'invoice',
        'name': 'Rechnungs-Generator',
        'icon': 'fa-file-invoice',
        'desc': 'Rechnungen gesammelt aus einer CSV-Datei als PDF erstellen',
        'demo': True
    },
    {
        'id': 'dashboard',
        'name': 'Dashboard',
        'icon': 'fa-chart-pie',
        'desc': 'Kennzahlen und Auswertungen auf einen Blick',
        'demo': True
    },
    {
        'id': 'schichtplan',
        'name': 'Schichtplaner',
        'icon': 'fa-clock',
        'desc': 'Schichtpläne einsehen und planen',
        'demo': True
    },
    {
        'id': 'trend-tracker',
        'name': 'Trend-Tracker',
        'icon': 'fa-chart-line',
        'desc': 'Nachfrage und Trends verfolgen und auswerten',
        'demo': True
    },
    {
        'id': 'todos',
        'name': 'To-Do Liste',
        'icon': 'fa-list',
        'desc': 'Tägliche und wöchentliche Team-Aufgaben verwalten'
    },
        {
        'id': 'ideas', 
        'name': 'Ideenpool', 
        'icon': 'fa-lightbulb', 
        'desc': 'Beschreibe Ideen für zukünftige Tools oder Verbesserungen'
    }
]

# Hilfsfunktion, um die Store.Konfiguration zu laden
def load_stores_config():
    with open('data/stores_config.json', 'r', encoding='utf-8') as f:
        return json.load(f)
    
# 0 Die Startseite: Auswahl der Stores
@app.route('/')
def index():
    config = load_stores_config()
    return render_template('store_selection.html', stores=config['stores'], store=None)

# 1. Startseite eines Stores (Übersicht aller Kacheln)
@app.route('/service/<int:store_id>')
def store_index(store_id):
    stores_config = load_stores_config()
    store_key = str(store_id)

    if store_key not in stores_config['stores']:
        return "Store nicht gefunden", 404
    else:
        store_info = stores_config['stores'][store_key]
        store_services = store_info.get('services', [])

        filter_SERVICES = [service for service in SERVICES if service['id'] in store_services]
        
        return render_template('index.html', services=filter_SERVICES, store=store_info, store_id=store_id, test=123)

# 2. Dashboard Route ("In Arbeit")
@app.route('/service/<int:store_id>/dashboard')
def dashboard_tool(store_id):
    return """
    <div style="font-family: sans-serif; text-align: center; padding: 50px; margin-top: 100px;">
        <i class="fas fa-tools" style="font-size: 48px; color: #f0ad4e; margin-bottom: 20px;"></i>
        <h2 style="color: #333;">Dashboard</h2>
        <p style="color: #666; font-size: 18px;">Dieser Service befindet sich aktuell noch <strong>in Arbeit</strong>.</p>
        <br>
        <a href="/" style="color: #0275d8; text-decoration: none; font-weight: bold;">← Zurück zum Mitarbeiter-Hub</a>
    </div>
    """

# 3. TODO-Liste Route
@app.route('/service/<int:store_id>/todos')
def todo_list(store_id):
    stores_config = load_stores_config()
    store_key = str(store_id)
    if store_key not in stores_config['stores']:
        return "Store nicht gefunden", 404
    store_info = stores_config['stores'][store_key]

    today = date.today()
    week_start = today - timedelta(days=today.weekday())  # Montag dieser Woche

    # --- Wochen-Todos (immer sichtbar, wöchentlicher Lazy Reset) ---
    woche_todos = Todo.query.filter_by(store_id=store_id, typ='wochentodo').all()
    for todo in woche_todos:
        if todo.erstellungsdatum < week_start:
            todo.erledigt = False
            todo.erstellungsdatum = today
    db.session.commit()

    # --- Tages-Todos laden und trennen ---
    tages_todos = Todo.query.filter_by(store_id=store_id, typ='tagestodo').all()
    wiederkehrende = [t for t in tages_todos if t.art == 'wiederkehrend']
    einmalige = [t for t in tages_todos if t.art == 'einmalig']

    # Lazy Reset für wiederkehrende Tages-Todos (täglich)
    for todo in wiederkehrende:
        if todo.erstellungsdatum < today:
            todo.erledigt = False
            todo.erstellungsdatum = today
    db.session.commit()

    # --- Wochentag-Sektionen aufbauen (Montag bis Samstag, Sonntag ausgeschlossen) ---
    wochentag_sektionen = []
    for i in range(6):
        tag_datum = week_start + timedelta(days=i)
        tag_name = WOCHENTAGE_DE[i]

        tag_todos = [t for t in einmalige if t.erledigungsdatum == tag_datum]

        # Wiederkehrende Todos nur am heutigen Tag selbst einblenden
        if tag_datum == today:
            tag_todos = tag_todos + wiederkehrende

        ist_vergangenheit = tag_datum < today
        alle_erledigt = all(t.erledigt for t in tag_todos) if tag_todos else True

        # Vergangene, komplett erledigte (oder leere) Tage ausblenden
        if ist_vergangenheit and alle_erledigt:
            continue

        if tag_datum == today:
            status_klasse = 'day-today'
        elif ist_vergangenheit:
            status_klasse = 'day-overdue'
        else:
            status_klasse = 'day-future'

        # Sortierung innerhalb des Tages: erst einmalige, dann wiederkehrende
        tag_todos_sortiert = (
            [t for t in tag_todos if t.art == 'einmalig'] +
            [t for t in tag_todos if t.art == 'wiederkehrend']
        )

        wochentag_sektionen.append({
            'name': tag_name,
            'datum': tag_datum,
            'todos': tag_todos_sortiert,
            'status_klasse': status_klasse,
        })

    return render_template(
        'todos.html',
        store=store_info,
        store_id=store_id,
        woche_todos=woche_todos,
        wochentag_sektionen=wochentag_sektionen,
        heute=today,
    )


@app.route('/service/<int:store_id>/todos/add', methods=['POST'])
def todo_add(store_id):
    titel = request.form.get('titel')
    text = request.form.get('text')
    kategorie = request.form.get('typ')  # 'tagestodo' oder 'wochentodo'

    if not titel or kategorie not in ('tagestodo', 'wochentodo'):
        return "Ungültige Eingabe", 400

    art = request.form.get('art') if kategorie == 'tagestodo' else None
    if art not in ('einmalig', 'wiederkehrend'):
        art = None

    erledigungsdatum = None
    if kategorie == 'tagestodo' and art == 'einmalig':
        erledigungsdatum_str = request.form.get('erledigungsdatum')
        if erledigungsdatum_str:
            erledigungsdatum = datetime.strptime(erledigungsdatum_str, '%Y-%m-%d').date()
            if erledigungsdatum.weekday() == 6:  # Sonntag serverseitig zusätzlich blocken
                return "Sonntag ist nicht wählbar", 400

    neues_todo = Todo(
        titel=titel,
        text=text,
        typ=kategorie,
        art=art,
        store_id=store_id,
        erledigt=False,
        erstellungsdatum=date.today(),
        erledigungsdatum=erledigungsdatum
    )
    db.session.add(neues_todo)
    db.session.commit()

    return redirect(url_for('todo_list', store_id=store_id))


@app.route('/service/<int:store_id>/todos/<int:todo_id>/edit', methods=['POST'])
def todo_edit(store_id, todo_id):
    todo = Todo.query.get_or_404(todo_id)

    kategorie = request.form.get('typ')
    if kategorie not in ('tagestodo', 'wochentodo'):
        return "Ungültige Eingabe", 400

    art = request.form.get('art') if kategorie == 'tagestodo' else None
    if art not in ('einmalig', 'wiederkehrend'):
        art = None

    erledigungsdatum = None
    if kategorie == 'tagestodo' and art == 'einmalig':
        erledigungsdatum_str = request.form.get('erledigungsdatum')
        if erledigungsdatum_str:
            erledigungsdatum = datetime.strptime(erledigungsdatum_str, '%Y-%m-%d').date()
            if erledigungsdatum.weekday() == 6:
                return "Sonntag ist nicht wählbar", 400

    todo.titel = request.form.get('titel')
    todo.text = request.form.get('text')
    todo.typ = kategorie
    todo.art = art
    todo.erledigungsdatum = erledigungsdatum
    db.session.commit()

    return redirect(url_for('todo_list', store_id=store_id))


@app.route('/service/<int:store_id>/todos/<int:todo_id>/toggle', methods=['POST'])
def todo_toggle(store_id, todo_id):
    todo = Todo.query.get_or_404(todo_id)
    todo.erledigt = not todo.erledigt
    db.session.commit()
    return redirect(url_for('todo_list', store_id=store_id))


@app.route('/service/<int:store_id>/todos/<int:todo_id>/delete', methods=['POST'])
def todo_delete(store_id, todo_id):
    todo = Todo.query.get_or_404(todo_id)
    db.session.delete(todo)
    db.session.commit()
    return redirect(url_for('todo_list', store_id=store_id))

if __name__ == '__main__':
    # use_reloader=False schaltet den Watchdog aus, damit es stabil startet
    app.run(debug=False, use_reloader=False, host='0.0.0.0', port=5000)