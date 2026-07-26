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

# ADICIONADO 'POST' AQUI PARA RECEBER O BOTÃO "SALVAR ALTERAÇÕES"
@presence_bp.route("/presence", methods=["GET", "POST"])
@login_required
def index():
    user_tipo = getattr(current_user, 'tipo', 'USER')
    if user_tipo not in ['MASTER', 'LIDER']:
        flash("Acesso restrito à área administrativa e de liderança.", "warning")
        return redirect(url_for("dashboard.index"))

    events = Event.query.order_by(Event.data.desc(), Event.id.desc()).all()
    
    # Gerencia parâmetros dependendo se o usuário está carregando a tela (GET) ou salvando (POST)
    if request.method == "POST":
        selected_event_id = request.form.get("event_id", type=int)
        if not selected_event_id:
            selected_event_id = request.args.get("event_id", type=int)
        departamento_selecionado = request.form.get("departamento_atual", "")
    else:
        selected_event_id = request.args.get("event_id", type=int)
        departamento_selecionado = request.args.get("departamento", "").strip()
    
    if not selected_event_id and events:
        selected_event_id = events[0].id

    selected_event = None
    members = []
    present_member_ids = []

    # Busca todos os departamentos únicos cadastrados para preencher o select do filtro
    departamentos_disponiveis = []
    if hasattr(Member, 'departamento'):
        deps = db.session.query(Member.departamento).filter(Member.departamento != None, Member.departamento != '').distinct().all()
        departamentos_disponiveis = [d[0] for d in deps]

    if selected_event_id:
        selected_event = Event.query.get_or_404(selected_event_id)
        
        query = Member.query
        if hasattr(Member, 'ativo'):
            query = query.filter_by(ativo=True)
        
        if departamento_selecionado and hasattr(Member, 'departamento'):
            query = query.filter_by(departamento=departamento_selecionado)
            
        members = query.order_by(Member.nome.asc()).all()
        
        # --- LÓGICA DE SALVAMENTO CIRÚRGICA (Igual a do Líder) ---
        if request.method == "POST":
            for member in members:
                nome_campo = f'presente_{member.id}'
                
                # Se o checkbox veio marcado no formulário, é True. Senão, é False.
                status = nome_campo in request.form
                
                att = Attendance.query.filter_by(event_id=selected_event.id, member_id=member.id).first()
                if att:
                    if hasattr(att, 'presente'):
                        att.presente = status
                    else:
                        if not status:
                            db.session.delete(att)
                else:
                    if status:
                        if hasattr(Attendance, 'presente'):
                            new_att = Attendance(event_id=selected_event.id, member_id=member.id, presente=True)
                        else:
                            new_att = Attendance(event_id=selected_event.id, member_id=member.id)
                        db.session.add(new_att)
            
            db.session.commit()
            flash("Chamada salva com sucesso!", "success")
            return redirect(url_for("presence.index", event_id=selected_event.id, departamento=departamento_selecionado))
        # -----------------------------------------------------------

        # Busca presenças atuais para exibir na tela (Sincronizado com a regra do Líder)
        attendances = Attendance.query.filter_by(event_id=selected_event_id).all()
        if hasattr(Attendance, 'presente'):
            present_member_ids = [a.member_id for a in attendances if getattr(a, 'presente', False)]
        else:
            present_member_ids = [a.member_id for a in attendances]

    next_sunday_str = get_next_sunday().strftime("%Y-%m-%d")

    return render_template(
        "presence.html", 
        events=events, 
        selected_event=selected_event, 
        members=members, 
        present_member_ids=present_member_ids,
        next_sunday_str=next_sunday_str,
        departamento_selecionado=departamento_selecionado,
        departamentos_disponiveis=departamentos_disponiveis
    )

@presence_bp.route("/events/quick_add_ebd", methods=["POST"])
@login_required
def quick_add_ebd():
    user_tipo = getattr(current_user, 'tipo', 'USER')
    if user_tipo not in ['MASTER', 'LIDER']:
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
    user_tipo = getattr(current_user, 'tipo', 'USER')
    if user_tipo not in ['MASTER', 'LIDER']:
        flash("Acesso negado.", "danger")
        return redirect(url_for("presence.index"))

    departamento_selecionado = request.args.get("departamento") or request.form.get("departamento", "")
    
    attendance = Attendance.query.filter_by(event_id=event_id, member_id=member_id).first()
    
    if attendance:
        if hasattr(attendance, 'presente'):
            attendance.presente = not attendance.presente
            flash(f"Presença alterada para {'Presente' if attendance.presente else 'Ausente'}.", "info")
        else:
            db.session.delete(attendance)
            flash("Presença removida.", "info")
    else:
        if hasattr(Attendance, 'presente'):
            new_attendance = Attendance(event_id=event_id, member_id=member_id, presente=True)
        else:
            new_attendance = Attendance(event_id=event_id, member_id=member_id)
        db.session.add(new_attendance)
        flash("Presença registrada!", "success")
        
    db.session.commit()
    return redirect(url_for("presence.index", event_id=event_id, departamento=departamento_selecionado))