import re
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from models import db
from models.user import User

auth_bp = Blueprint('auth', __name__)

# --- Rota de Login ---
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        raw_cpf = request.form.get('cpf', '')
        senha = request.form.get('senha', '')
        
        # Limpa o CPF digitado
        cpf_limpo = re.sub(r'\D', '', raw_cpf)
        
        user = User.query.filter_by(cpf=cpf_limpo).first()

        # Validação flexível: aceita a senha correta OU se a senha digitada for igual ao CPF limpo
        if user and (user.check_password(senha) or senha == cpf_limpo):
            if not getattr(user, 'ativo', True):
                flash('Sua conta está desativada. Procure o Administrador.', 'danger')
                return redirect(url_for('auth.login'))

            login_user(user)
            
            if getattr(user, 'tipo', 'USER') == 'MASTER':
                return redirect(url_for('dashboard.index'))
            else:
                return redirect(url_for('presence.index'))
        else:
            flash('CPF ou senha incorretos.', 'danger')

    return render_template('login.html')

# --- Rota: Cadastrar novo usuário (Apenas Admin/Master) ---
@auth_bp.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    if getattr(current_user, 'tipo', None) != 'MASTER':
        flash('Acesso não permitido.', 'danger')
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        nome = request.form.get('nome')
        raw_cpf = request.form.get('cpf', '')
        email = request.form.get('email')
        tipo = request.form.get('tipo', 'USER')

        cpf_limpo = re.sub(r'\D', '', raw_cpf)

        if User.query.filter_by(cpf=cpf_limpo).first():
            flash('CPF já cadastrado no sistema!', 'warning')
            return redirect(url_for('auth.register'))

        novo_usuario = User(
            nome=nome,
            cpf=cpf_limpo,
            email=email,
            tipo=tipo,
            ativo=True
        )
        novo_usuario.set_password(cpf_limpo)

        db.session.add(novo_usuario)
        db.session.commit()

        flash(f'Usuário {nome} criado com sucesso!', 'success')
        return redirect(url_for('dashboard.index'))

    return render_template('register.html')

# --- Rota de Logout ---
@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))