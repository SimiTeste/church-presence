from models import db
from datetime import datetime
import re
from sqlalchemy.orm import validates

class Member(db.Model):
    __tablename__ = 'members'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    cpf = db.Column(db.String(11), unique=True, nullable=True)
    telefone = db.Column(db.String(20), nullable=True)
    foto = db.Column(db.String(255), default='default.png')
    departamento = db.Column(db.String(50), default='Geral')
    sexo = db.Column(db.String(10), nullable=True)
    ativo = db.Column(db.Boolean, default=True)
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow)

    @validates('cpf')
    def validate_cpf(self, key, cpf_value):
        if not cpf_value:
            return None
        return re.sub(r'\D', '', cpf_value)