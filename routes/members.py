from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from models import db
from models.member import Member

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
        
        if not nome or not cpf:
            flash('Nome e CPF são obrigatórios.', 'danger')
            return redirect(url_for('members.new'))
            
        existing = Member.query.filter_by(cpf=cpf).first()
        if existing:
            flash('Já existe um membro cadastrado com este CPF.', 'danger')
            return redirect(url_for('members.new'))
            
        new_member = Member(nome=nome, cpf=cpf, telefone=telefone, departamento=departamento)
        db.session.add(new_member)
        db.session.commit()
        
        flash('Membro cadastrado com sucesso!', 'success')
        return redirect(url_for('members.index'))
        
    return render_template('edit_member.html', member=None)

@members_bp.route('/members/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    member = Member.query.get_or_404(id)
    
    if request.method == 'POST':
        member.nome = request.form.get('nome')
        member.cpf = request.form.get('cpf')
        member.telefone = request.form.get('telefone')
        member.departamento = request.form.get('departamento')
        
        db.session.commit()
        flash('Membro atualizado com sucesso!', 'success')
        return redirect(url_for('members.index'))
        
    return render_template('edit_member.html', member=member)

@members_bp.route('/members/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    member = Member.query.get_or_404(id)
    db.session.delete(member)
    db.session.commit()
    flash('Membro excluído com sucesso!', 'success')
    return redirect(url_for('members.index'))