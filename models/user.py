from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from models import db

class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    cpf = db.Column(db.String(14), unique=True, nullable=True)
    senha = db.Column(db.String(255), nullable=True)
    tipo = db.Column(db.String(20), default="USER")
    ativo = db.Column(db.Boolean, default=True)

    def set_password(self, password):
        self.senha = generate_password_hash(password)

    # Alias/apelido para aceitar set_senha tambem
    def set_senha(self, password):
        self.set_password(password)

    def check_password(self, password):
        if not self.senha:
            return False
        if self.senha.startswith("scrypt:") or self.senha.startswith("pbkdf2:"):
            return check_password_hash(self.senha, password)
        return self.senha == password