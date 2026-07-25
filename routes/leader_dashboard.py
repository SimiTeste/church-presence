from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db
from models.notice import Notice
from models.member import Member
from models.attendance import Event, Attendance

leader_bp = Blueprint('leader', __name__)

def check_leader():
    return current_user.is_authenticated and current_user.tipo in ["LIDER", "MASTER"]

@leader_bp.route('/leader/dashboard')
@login_required
def dashboard():
    if not check_leader():
        flash('Acesso negado. Área restrita para líderes.', 'danger')
        return redirect(url_for('dashboard.index'))
        
    avisos = Notice.query.order_by(Notice.data_criacao.desc()).all()
    eventos = Event.query.all()
    return render_template('dashboard_lider.html', avisos=avisos, eventos=eventos)

@leader_bp.route('/leader/avisos/novo', methods=['POST'])
@login_required
def criar_aviso():
    if not check_leader():
        flash('Acesso negado.', 'danger')
        return redirect(url_for('auth.login'))
        
    titulo = request.form.get('titulo')
    conteudo = request.form.get('conteudo')
    
    if not titulo or not conteudo:
        flash('Título e conteúdo do aviso são obrigatórios.', 'danger')
        return redirect(url_for('leader.dashboard'))
        
    novo_aviso = Notice(
        titulo=titulo,
        conteudo=conteudo
    )
    db.session.add(novo_aviso)
    db.session.commit()
    
    flash('Aviso enviado com sucesso!', 'success')
    return redirect(url_for('leader.dashboard'))

@leader_bp.route('/leader/chamada/<int:event_id>', methods=['GET', 'POST'])
@login_required
def chamada(event_id):
    if not check_leader():
        flash('Acesso negado.', 'danger')
        return redirect(url_for('auth.login'))
        
    evento = Event.query.get_or_404(event_id)
    membros = Member.query.filter_by(ativo=True).all()
    
    if request.method == 'POST':
        for membro in membros:
            status = request.form.get(f'presente_{membro.id}') == 'on'
            
            att = Attendance.query.filter_by(event_id=evento.id, member_id=membro.id).first()
            if att:
                att.presente = status
            else:
                att = Attendance(event_id=evento.id, member_id=membro.id, presente=status)
                db.session.add(att)
        
        db.session.commit()
        flash('Chamada salva com sucesso!', 'success')
        return redirect(url_for('leader.dashboard'))
        
    return render_template('realizar_chamada.html', evento=evento, membros=membros)