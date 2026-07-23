import os
import re
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required
from werkzeug.utils import secure_filename
from models import db
from models.member import Member
from models.user import User

members_bp = Blueprint("members", __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@members_bp.route("/members", methods=["GET"])
@login_required
def index():
    search = request.args.get("search", "").strip()
    departamento_selecionado = request.args.get("departamento", "").strip()
    
    query = Member.query
    
    # Filtro por texto (busca)
    if search:
        query = query.filter(Member.nome.ilike(f"%{search}%"))
        
    # Filtro por departamento
    if departamento_selecionado:
        query = query.filter_by(departamento=departamento_selecionado)
        
    members = query.order_by(Member.nome.asc()).all()
    
    return render_template(
        "members.html", 
        members=members, 
        search=search, 
        departamento_selecionado=departamento_selecionado
    )

@members_bp.route("/members/add", methods=["POST"])
@login_required
def add():
    nome = request.form.get("nome")
    raw_cpf = request.form.get("cpf", "")
    telefone = request.form.get("telefone")
    departamento = request.form.get("departamento")
    sexo = request.form.get("sexo")
    
    # Captura se o checkbox de liberar acesso foi marcado
    liberar_acesso = True if request.form.get("liberar_acesso") == "on" else False

    cpf_limpo = re.sub(r"\D", "", raw_cpf) if raw_cpf else None

    if cpf_limpo and Member.query.filter_by(cpf=cpf_limpo).first():
        flash("CPF já cadastrado para outro membro.", "danger")
        return redirect(url_for("members.index"))

    filename = "default.png"
    if 'foto' in request.files:
        file = request.files['foto']
        if file and file.filename != '' and allowed_file(file.filename):
            sec_filename = secure_filename(file.filename)
            filename = f"{cpf_limpo or 'membro'}_{sec_filename}"
            upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'])
            os.makedirs(upload_path, exist_ok=True)
            file.save(os.path.join(upload_path, filename))

    try:
        # 1. Cria o membro
        new_member = Member(
            nome=nome,
            cpf=cpf_limpo,
            telefone=telefone,
            departamento=departamento,
            sexo=sexo,
            foto=filename
        )
        db.session.add(new_member)
        db.session.flush() # Garante que o ID do membro seja gerado para o relacionamento

        # 2. Cria o Usuário de acesso APENAS se a opção "liberar_acesso" estiver marcada
        if liberar_acesso and cpf_limpo and not User.query.filter_by(cpf=cpf_limpo).first():
            email_padrao = f"{cpf_limpo}@church.com"
            new_user = User(
                nome=nome,
                cpf=cpf_limpo,
                email=email_padrao,
                tipo="USER",      # Define como usuário comum
                ativo=True
            )
            if hasattr(User, 'member_id'):
                new_user.member_id = new_member.id
                
            new_user.set_password(cpf_limpo) # Senha padrão inicial é o CPF do membro
            db.session.add(new_user)

        db.session.commit()
        
        mensagem = "Membro cadastrado com sucesso!"
        if liberar_acesso:
            mensagem += " Acesso de usuário gerado com o CPF."
        flash(mensagem, "success")
        
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao cadastrar membro: {e}", "danger")

    return redirect(url_for("members.index"))

@members_bp.route("/members/edit/<int:member_id>", methods=["GET", "POST"])
@login_required
def edit_member(member_id):
    member = Member.query.get_or_404(member_id)
    
    if request.method == "POST":
        member.nome = request.form.get("nome")
        member.telefone = request.form.get("telefone")
        member.departamento = request.form.get("departamento")
        member.sexo = request.form.get("sexo")
        member.ativo = True if request.form.get("ativo") == "on" else False
        
        # Tratamento opcional de nova foto na edição
        if 'foto' in request.files:
            file = request.files['foto']
            if file and file.filename != '' and allowed_file(file.filename):
                sec_filename = secure_filename(file.filename)
                filename = f"{member.cpf or 'membro'}_{sec_filename}"
                upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'])
                os.makedirs(upload_path, exist_ok=True)
                file.save(os.path.join(upload_path, filename))
                member.foto = filename

        db.session.commit()
        
        # Opcional: Atualiza também os dados do usuário vinculado se existir
        if member.cpf:
            user_relacionado = User.query.filter_by(cpf=member.cpf).first()
            if user_relacionado:
                user_relacionado.nome = member.nome
                user_relacionado.ativo = member.ativo
                db.session.commit()

        flash("Membro atualizado com sucesso!", "success")
        return redirect(url_for("members.index"))
        
    return render_template("edit_member.html", member=member)

@members_bp.route("/members/delete/<int:member_id>", methods=["POST"])
@login_required
def delete(member_id):
    member = Member.query.get_or_404(member_id)
    
    # Remove também o usuário vinculado se existir
    if member.cpf:
        user_relacionado = User.query.filter_by(cpf=member.cpf).first()
        if user_relacionado:
            db.session.delete(user_relacionado)

    db.session.delete(member)
    db.session.commit()
    flash("Membro e acesso removidos com sucesso!", "warning")
    return redirect(url_for("members.index"))