from datetime import datetime, timedelta
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db
from models.member import Member
from models.attendance import Event, Attendance

presence_bp = Blueprint("presence", __name__)

def get_next_sunday():
    today = datetime.now().date()
    days_until_sunday = (6 - today.weekday()) % 7
    return today + timedelta(days=days_until_sunday)

@presence_bp.route("/presence", methods=["GET"])
@login_required
def index():
    # Se o usuário não for MASTER, restringe o acesso e redireciona para o painel
    if getattr(current_user, 'tipo', 'USER') != 'MASTER':
        flash("Acesso restrito à área administrativa.", "warning")
        return redirect(url_for("dashboard.index"))

    events = Event.query.order_by(Event.data.desc(), Event.id.desc()).all()
    selected_event_id = request.args.get("event_id", type=int)
    departamento_selecionado = request.args.get("departamento", "").strip()
    
    # Se nenhum evento foi selecionado, mas existem eventos, seleciona o mais recente por padrão
    if not selected_event_id and events:
        selected_event_id = events[0].id

    selected_event = None
    members = []
    present_member_ids = []

    if selected_event_id:
        selected_event = Event.query.get_or_404(selected_event_id)
        
        # Consulta base de membros (ajustado caso o campo ativo não exista em todos os models)
        query = Member.query
        if hasattr(Member, 'ativo'):
            query = query.filter_by(ativo=True)
        
        # Aplica o filtro de departamento se selecionado
        if departamento_selecionado and hasattr(Member, 'departamento'):
            query = query.filter_by(departamento=departamento_selecionado)
            
        members = query.order_by(Member.nome.asc()).all()
        present_member_ids = [a.member_id for a in Attendance.query.filter_by(event_id=selected_event_id).all()]

    next_sunday_str = get_next_sunday().strftime("%Y-%m-%d")

    return render_template(
        "presence.html", 
        events=events, 
        selected_event=selected_event, 
        members=members, 
        present_member_ids=present_member_ids,
        next_sunday_str=next_sunday_str,
        departamento_selecionado=departamento_selecionado
    )

@presence_bp.route("/events/quick_add_ebd", methods=["POST"])
@login_required
def quick_add_ebd():
    if getattr(current_user, 'tipo', 'USER') != 'MASTER':
        flash("Acesso negado.", "danger")
        return redirect(url_for("presence.index"))

    next_sunday = get_next_sunday()
    nome_evento = "Escola Bíblica Dominical (EBD)"
    
    existing = Event.query.filter_by(nome=nome_evento, data=next_sunday).first()
    if existing:
        flash("A EBD deste domingo já foi criada!", "info")
        return redirect(url_for("presence.index", event_id=existing.id))

    new_event = Event(nome=nome_evento, data=next_sunday, descricao=f"Chamada EBD - {next_sunday.strftime('%d/%m/%Y')}")
    db.session.add(new_event)
    db.session.commit()
    
    flash(f"EBD criada com sucesso para {next_sunday.strftime('%d/%m/%Y')}!", "success")
    return redirect(url_for("presence.index", event_id=new_event.id))

@presence_bp.route("/presence/toggle/<int:event_id>/<int:member_id>", methods=["POST"])
@login_required
def toggle_presence(event_id, member_id):
    if getattr(current_user, 'tipo', 'USER') != 'MASTER':
        flash("Acesso negado.", "danger")
        return redirect(url_for("presence.index"))

    # Captura o departamento atual da URL ou do formulário para manter o filtro ativo
    departamento_selecionado = request.args.get("departamento") or request.form.get("departamento", "")
    
    attendance = Attendance.query.filter_by(event_id=event_id, member_id=member_id).first()
    
    if attendance:
        db.session.delete(attendance)
        flash("Presença removida.", "info")
    else:
        new_attendance = Attendance(event_id=event_id, member_id=member_id)
        db.session.add(new_attendance)
        flash("Presença registrada!", "success")
        
    db.session.commit()
    return redirect(url_for("presence.index", event_id=event_id, departamento=departamento_selecionado))