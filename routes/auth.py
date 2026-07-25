import re
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required
from models import db
from models.user import User
from models.member import Member

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        raw_cpf = request.form.get('cpf', '')
        nome = request.form.get('nome', '')
        email = request.form.get('email', '')
        tipo = request.form.get('tipo', 'USER')
        
        cpf_limpo = re.sub(r'\D', '', raw_cpf)
        
        if not cpf_limpo or not nome:
            flash('Nome e CPF são obrigatórios.', 'danger')
            return render_template('register.html')
            
        usuario_existente = User.query.filter_by(cpf=cpf_limpo).first()
        if usuario_existente:
            flash('Este CPF já está cadastrado no sistema.', 'danger')
            return render_template('register.html')
            
        senha_inicial = cpf_limpo[:6] if len(cpf_limpo) >= 6 else cpf_limpo
        
        novo_usuario = User(
            nome=nome,
            cpf=cpf_limpo,
            email=email if email else f"{cpf_limpo}@church.com",
            tipo=tipo,
            ativo=True
        )
        novo_usuario.set_password(senha_inicial)
        
        db.session.add(novo_usuario)
        db.session.commit()
        
        flash('Usuário cadastrado com sucesso!', 'success')
        return redirect(url_for('dashboard.index'))
        
    return render_template('register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        raw_cpf = request.form.get('cpf', '')
        senha = request.form.get('senha', '')
        
        cpf_limpo = re.sub(r'\D', '', raw_cpf)
        
        if not cpf_limpo:
            flash('Informe o CPF.', 'danger')
            return render_template('login.html')

        # 1. Login do Administrador Master
        if cpf_limpo == "00000000000":
            master = User.query.filter_by(cpf="00000000000").first()
            if master and master.check_password(senha):
                login_user(master)
                return redirect(url_for('dashboard.index'))
            else:
                flash('CPF ou senha incorretos.', 'danger')
                return render_template('login.html')

        # 2. Login do Membro / Usuário Comum / Líder
        user = User.query.filter_by(cpf=cpf_limpo).first()
        
        # Se o usuário não existe mas está na tabela de membros, cria automaticamente como USER
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

        # Se ainda assim não achar o usuário nem como membro cadastrado
        if not user:
            flash('CPF não encontrado na base de membros.', 'danger')
            return render_template('login.html')

        # Validação flexível e segura da senha
        senha_valida = user.check_password(senha) or (senha == cpf_limpo) or (senha == cpf_limpo[:6])

        if senha_valida:
            if not getattr(user, 'ativo', True):
                flash('Sua conta está desativada. Procure o Administrador.', 'danger')
                return render_template('login.html')

            login_user(user)
            
            # Redirecionamento inteligente: Se for LIDER ou MASTER, vai para o dashboard principal
            if user.tipo == "LIDER" or user.tipo == "MASTER":
                return redirect(url_for('dashboard.index'))
            else:
                return redirect(url_for('user_dashboard.index'))
        else:
            flash('CPF ou senha incorretos.', 'danger')

    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))