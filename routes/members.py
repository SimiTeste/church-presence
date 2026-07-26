from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db
from models.member import Member
from models.user import User  # <--- Importação essencial para sincronizar o login

members_bp = Blueprint('members', __name__)

@members_bp.route('/members')
@login_required
def index():
    departamento_selecionado = request.args.get('departamento')
    page = request.args.get('page', 1, type=int)
    per_page = 10

    query = Member.query
    if departamento_selecionado:
        query = query.filter_by(departamento=departamento_selecionado)
        
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    members = pagination.items
    
    return render_template('members.html', members=members, pagination=pagination, departamento_selecionado=departamento_selecionado)

@members_bp.route('/members/new', methods=['GET', 'POST'])
@login_required
def new():
    if request.method == 'POST':
        nome = request.form.get('nome')
        cpf = request.form.get('cpf')
        telefone = request.form.get('telefone')
        departamento = request.form.get('departamento')
        tipo = request.form.get('tipo', 'USER')
        
        if not nome or not cpf:
            flash('Nome e CPF são obrigatórios.', 'danger')
            return redirect(url_for('members.new'))
            
        existing = Member.query.filter_by(cpf=cpf).first()
        if existing:
            flash('Já existe um membro cadastrado com este CPF.', 'danger')
            return redirect(url_for('members.new'))
            
        # 1. Cria o Membro
        new_member = Member(
            nome=nome, 
            cpf=cpf, 
            telefone=telefone, 
            departamento=departamento, 
            tipo=tipo
        )
        db.session.add(new_member)

        # 2. Sincroniza ou cria o Usuário correspondente para o Login funcionar certo
        user_obj = User.query.filter_by(cpf=cpf).first()
        if not user_obj:
            user_obj = User(
                nome=nome,
                cpf=cpf,
                email=f"{cpf}@church.com",
                tipo=tipo,
                ativo=True
            )
            user_obj.set_password(cpf) # Senha padrão inicial é o próprio CPF
            db.session.add(user_obj)
        else:
            user_obj.nome = nome
            user_obj.tipo = tipo
            user_obj.ativo = True
            db.session.add(user_obj)

        db.session.commit()
        
        flash('Membro e usuário cadastrados com sucesso!', 'success')
        return redirect(url_for('members.index'))
        
    return render_template('edit_member.html', member=None)

@members_bp.route('/members/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    member = Member.query.get_or_404(id)
    cpf_antigo = member.cpf
    
    if request.method == 'POST':
        member.nome = request.form.get('nome')
        member.cpf = request.form.get('cpf')
        member.telefone = request.form.get('telefone')
        member.departamento = request.form.get('departamento')
        member.tipo = request.form.get('tipo', 'USER')
        
        # Sincroniza também na tabela User pelo CPF (antigo ou novo)
        user_obj = User.query.filter_by(cpf=cpf_antigo).first()
        if not user_obj:
            user_obj = User.query.filter_by(cpf=member.cpf).first()

        if user_obj:
            user_obj.nome = member.nome
            user_obj.cpf = member.cpf
            user_obj.tipo = member.tipo
            db.session.add(user_obj)
        else:
            # Se por acaso não existir usuário para ele, cria um
            user_obj = User(
                nome=member.nome,
                cpf=member.cpf,
                email=f"{member.cpf}@church.com",
                tipo=member.tipo,
                ativo=True
            )
            user_obj.set_password(member.cpf)
            db.session.add(user_obj)
            
        db.session.commit()
        flash('Membro e permissões de acesso atualizados com sucesso!', 'success')
        return redirect(url_for('members.index'))
        
    return render_template('edit_member.html', member=member)

@members_bp.route('/members/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    member = Member.query.get_or_404(id)
    user_obj = User.query.filter_by(cpf=member.cpf).first()
    if user_obj and user_obj.tipo != "MASTER":
        db.session.delete(user_obj)
        
    db.session.delete(member)
    db.session.commit()
    flash('Membro excluído com sucesso!', 'success')
    return redirect(url_for('members.index'))

@members_bp.route('/meu-perfil', methods=['GET', 'POST'])
@login_required
def meu_perfil():
    # Busca o membro logado utilizando o CPF do usuário atual da sessão
    member = Member.query.filter_by(cpf=current_user.cpf).first_or_404()
    
    if request.method == 'POST':
        # Atualiza os dados permitidos para alteração autônoma do próprio usuário
        member.nome = request.form.get('nome')
        member.telefone = request.form.get('telefone')
        
        # Sincroniza instantaneamente as alterações na tabela User correspondente
        user_obj = User.query.filter_by(cpf=member.cpf).first()
        if user_obj:
            user_obj.nome = member.nome
            db.session.add(user_obj)
            
        db.session.commit()
        flash('Seus dados foram atualizados com sucesso!', 'success')
        return redirect(url_for('members.meu_perfil'))
        
    return render_template('meu_perfil.html', member=member)