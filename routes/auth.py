from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from models import db
from models.user import User

auth_bp = Blueprint('auth', __name__)

# --- Rota de Login Existente ---
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        cpf = request.form.get('cpf')
        senha = request.form.get('senha')
        user = User.query.filter_by(cpf=cpf).first()

        if user and user.check_password(senha):
            login_user(user)
            return redirect(url_for('dashboard.index'))
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
        cpf = request.form.get('cpf', '').replace('.', '').replace('-', '').strip()
        email = request.form.get('email')
        tipo = request.form.get('tipo', 'USER')

        if User.query.filter_by(cpf=cpf).first():
            flash('CPF já cadastrado no sistema!', 'warning')
            return redirect(url_for('auth.register'))

        # A senha inicial será os 6 primeiros dígitos do CPF
        senha_inicial = cpf[:6] if len(cpf) >= 6 else '123456'

        novo_usuario = User(
            nome=nome,
            cpf=cpf,
            email=email,
            tipo=tipo,
            ativo=True
        )
        novo_usuario.set_password(senha_inicial)

        db.session.add(novo_usuario)
        db.session.commit()

        flash(f'Usuário {nome} criado! A senha inicial é: {senha_inicial}', 'success')
        return redirect(url_for('dashboard.index'))

    return render_template('register.html')

# --- Rota de Logout ---
@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))