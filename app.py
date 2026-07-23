import os
from flask import Flask, redirect, url_for
from config import Config
from models import db
from models.user import User
from models.member import Member
from models.attendance import Event, Attendance
from flask_login import LoginManager
from flask_migrate import Migrate

from routes.auth import auth_bp
from routes.dashboard import dashboard_bp
from routes.members import members_bp
from routes.presence import presence_bp
from routes.reports import reports_bp

app = Flask(__name__)
app.config.from_object(Config)

# Ajuste crítico para o Render: corrige a URL do PostgreSQL se necessário
database_url = os.getenv('DATABASE_URL')
if database_url:
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url

db.init_app(app)
migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "auth.login"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

app.register_blueprint(auth_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(members_bp)
app.register_blueprint(presence_bp)
app.register_blueprint(reports_bp)

# Rota raiz para evitar erro 404 ao acessar o link principal
@app.route('/')
def index():
    return redirect(url_for('auth.login'))

# Criacao de tabelas e usuario Master inicial
with app.app_context():
    db.create_all()
    try:
        if not User.query.filter_by(cpf="00000000000").first():
            master = User(
                nome="Administrador Master",
                cpf="00000000000",
                email="admin@church.com",
                tipo="MASTER",
                ativo=True
            )
            master.set_password("admin123")
            db.session.add(master)
            db.session.commit()
            print(">>> Usuario Master criado com sucesso! <<<")
    except Exception as e:
        db.session.rollback()
        print(f">>> Erro ao inicializar usuario master: {e} <<<")

if __name__ == "__main__":
    app.run(debug=True)