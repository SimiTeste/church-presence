import re
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from models import db
from models.user import User
from models.member import Member

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        raw_cpf = request.form.get('cpf', '')
        senha = request.form.get('senha', '')
        
        cpf_limpo = re.sub(r'\D', '', raw_cpf)
        
        if not cpf_limpo:
            flash('Informe o CPF.', 'danger')
            return render_template('login.html')

        # 1. Tenta achar o usuario na tabela User
        user = User.query.filter_by(cpf=cpf_limpo).first()

        # 2. Se nao existe na tabela User, mas existe na tabela Member, cria o User agora
        if not user:
            membro = Member.query.filter_by(cpf=cpf_limpo).first()
            if membro:
                user = User(
                    nome=membro.nome,
                    cpf=cpf_limpo,
                    email=f"{cpf_limpo}@church.com",
                    tipo="USER",
                    ativo=True
                )
                user.set_password(cpf_limpo)
                db.session.add(user)
                db.session.commit()

        # 3. Valida o login (Master ou senha igual ao CPF ou senha cadastrada)
        if user and (user.check_password(senha) or senha == cpf_limpo or user.tipo == 'MASTER'):
            if not getattr(user, 'ativo', True):
                flash('Sua conta está desativada. Procure o Administrador.', 'danger')
                return redirect(url_for('auth.login'))

            login_user(user)
            
            if user.tipo == 'MASTER':
                return redirect(url_for('dashboard.index'))
            else:
                return redirect(url_for('presence.index'))
        else:
            flash('CPF ou senha incorretos.', 'danger')

    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))