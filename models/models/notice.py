from models import db
from datetime import datetime

class Notice(db.Model):
    __tablename__ = 'notices'
    
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(150), nullable=False)
    conteudo = db.Column(db.Text, nullable=False)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    ativo = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f"<Notice {self.titulo}>"