from datetime import date
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Todo(db.Model):
    __tablename__ = 'todos'
    
    id = db.Column(db.Integer, primary_key=True)
    titel = db.Column(db.String(100), nullable=False)
    text = db.Column(db.String(500), nullable=True)
    typ = db.Column(db.String(10), nullable=False)          # 'tagestodo' | 'wochentodo'
    art = db.Column(db.String(15), nullable=True)            # 'einmalig' | 'wiederkehrend'
    store_id = db.Column(db.Integer, nullable=False)
    erledigt = db.Column(db.Boolean, default=False, nullable=False)
    erstellungsdatum = db.Column(db.Date, default=date.today, nullable=False)
    erledigungsdatum = db.Column(db.Date, nullable=True)