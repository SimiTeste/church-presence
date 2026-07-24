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
from routes.user_dashboard import user_dashboard_bp

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
app.register_blueprint(user_dashboard_bp)

# Rota raiz para evitar erro 404 ao acessar o link principal
@app.route('/')
def index():
    return redirect(url_for('auth.login'))

# Criacao de tabelas, atualizacao de esquema e usuario Master inicial
with app.app_context():
    db.create_all()
    try:
        # Garante que o usuario Master sempre exista e esteja atualizado
        master = User.query.filter_by(cpf="00000000000").first()
        if not master:
            master = User(
                nome="Administrador Master",
                cpf="00000000000",
                email="admin@church.com",
                tipo="MASTER",
                ativo=True
            )
            master.set_password("admin123")
            db.session.add(master)
            print(">>> Usuario Master criado com sucesso! <<<")
        else:
            master.tipo = "MASTER"
            master.ativo = True
            db.session.add(master)

        # Força a criação do membro e usuário de teste para o CPF 51070144886
        teste_cpf = "51070144886"
        membro_teste = Member.query.filter_by(cpf=teste_cpf).first()
        if not membro_teste:
            membro_teste = Member(
                nome="Membro de Teste",
                cpf=teste_cpf,
                departamento="Geral",
                ativo=True
            )
            db.session.add(membro_teste)
            print(">>> Membro de teste criado com sucesso! <<<")

        usuario_teste = User.query.filter_by(cpf=teste_cpf).first()
        if not usuario_teste:
            usuario_teste = User(
                nome="Membro de Teste",
                cpf=teste_cpf,
                email=f"{teste_cpf}@church.com",
                tipo="USER",
                ativo=True
            )
            usuario_teste.set_password(teste_cpf)
            db.session.add(usuario_teste)
            print(">>> Usuário de teste criado com sucesso! <<<")
        else:
            usuario_teste.set_password(teste_cpf)
            usuario_teste.ativo = True
            db.session.add(usuario_teste)
            
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f">>> Erro ao inicializar usuario master/teste: {e} <<<")

if __name__ == "__main__":
    app.run(debug=True)