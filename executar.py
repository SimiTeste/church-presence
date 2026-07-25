import os
os.environ["DATABASE_URL"] = "postgresql://db_church_lbz8_user:C0YsHYUOPMfyMmfeUiymDJKd9Q9XlIZF@dpg-d9hamd58nd3s73cknvug-a.oregon-postgres.render.com/db_church_lbz8"

from app import app
from models import db
from sqlalchemy import text

with app.app_context():
    db.session.execute(text("ALTER TABLE members ADD COLUMN IF NOT EXISTS tipo VARCHAR(50) DEFAULT 'USER';"))
    db.session.execute(text("ALTER TABLE members ADD COLUMN IF NOT EXISTS foto VARCHAR(255);"))
    db.session.execute(text("ALTER TABLE members ADD COLUMN IF NOT EXISTS sexo VARCHAR(20);"))
    db.session.execute(text("ALTER TABLE members ADD COLUMN IF NOT EXISTS ativo BOOLEAN DEFAULT TRUE;"))
    db.session.commit()
    print("Atualizado com sucesso!")