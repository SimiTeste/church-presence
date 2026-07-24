import re
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required
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

        # 1. Se for o Administrador Master
        if cpf_limpo == "00000000000":
            master = User.query.filter_by(cpf="00000000000").first()
            if master and master.check_password(senha):
                login_user(master)
                return redirect(url_for('dashboard.index'))
            else:
                flash('CPF ou senha incorretos.', 'danger')
                return render_template('login.html')

        # 2. Verifica se o CPF existe na tabela de Membros
        membro = Member.query.filter_by(cpf=cpf_limpo).first()
        if not membro:
            flash('CPF ou senha incorretos.', 'danger')
            return render_template('login.html')

        # 3. Se o membro existe, busca ou cria o usuário correspondente
        user = User.query.filter_by(cpf=cpf_limpo).first()
        if not user:
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
        else:
            # Garante que a senha e o status estejam corretos para o membro logar
            user.set_password(cpf_limpo)
            user.ativo = True
            db.session.commit()

        # 4. Efetua o login do usuário comum
        login_user(user)
        return redirect(url_for('presence.index'))

    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))