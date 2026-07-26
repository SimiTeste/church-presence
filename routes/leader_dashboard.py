from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db
from models.notice import Notice
from models.member import Member
from models.attendance import Event, Attendance
from sqlalchemy import func

leader_bp = Blueprint('leader', __name__)

@leader_bp.route('/leader/dashboard')
@login_required
def dashboard():
    if not current_user.is_authenticated or current_user.tipo not in ["MASTER", "LIDER"]:
        flash('Acesso negado. Área restrita.', 'danger')
        return redirect(url_for('dashboard.index'))
        
    avisos = Notice.query.order_by(Notice.data_criacao.desc()).all()
    eventos = Event.query.all()
    
    ranking_membros = db.session.query(
        Member, 
        func.count(Attendance.id).label('total_presencas')
    ).outerjoin(Attendance, (Attendance.member_id == Member.id) & (Attendance.presente == True))\
     .filter(Member.ativo == True)\
     .group_by(Member.id)\
     .order_by(func.count(Attendance.id).desc())\
     .all()

    return render_template(
        'dashboard_lider.html', 
        avisos=avisos, 
        eventos=eventos, 
        ranking_membros=ranking_membros
    )

@leader_bp.route('/leader/avisos/novo', methods=['POST'])
@login_required
def criar_aviso():
    if not current_user.is_authenticated or current_user.tipo not in ["MASTER", "LIDER"]:
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

@leader_bp.route('/leader/chamada', defaults={'event_id': None}, methods=['GET', 'POST'])
@leader_bp.route('/leader/chamada/<int:event_id>', methods=['GET', 'POST'])
@login_required
def chamada(event_id):
    if not current_user.is_authenticated or current_user.tipo not in ["MASTER", "LIDER", "COMUM", "USUARIO"]:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('auth.login'))
        
    eventos = Event.query.order_by(Event.data.desc()).all()
    
    if not eventos:
        flash('Nenhum evento cadastrado.', 'warning')
        return redirect(url_for('leader.dashboard'))
        
    if event_id is None:
        return redirect(url_for('leader.chamada', event_id=eventos[0].id))
        
    evento = Event.query.get_or_404(event_id)
    
    departamento_filtro = request.args.get('departamento', '')
    if request.method == 'POST':
        departamento_filtro = request.form.get('departamento_atual', '')

    query = Member.query.filter_by(ativo=True)
    if departamento_filtro:
        query = query.filter_by(departamento=departamento_filtro)
    membros = query.all()
    
    departamentos = db.session.query(Member.departamento).filter(Member.departamento != '').distinct().all()
    departamentos = [d[0] for d in departamentos if d[0]]
    
    if request.method == 'POST':
        # Atualiza APENAS os membros que estavam renderizados e submetidos na tela atual
        for membro in membros:
            nome_campo = f'presente_{membro.id}'
            
            # CORREÇÃO: Se o checkbox vem no formulário, significa que foi marcado (True). 
            # Se não vem, o navegador ocultou porque o switch estava desligado (False).
            status = nome_campo in request.form
            
            att = Attendance.query.filter_by(event_id=evento.id, member_id=membro.id).first()
            if att:
                att.presente = status
            else:
                att = Attendance(event_id=evento.id, member_id=membro.id, presente=status)
                db.session.add(att)
        
        db.session.commit()
        flash('Chamada salva com sucesso!', 'success')
        return redirect(url_for('leader.chamada', event_id=evento.id, departamento=departamento_filtro))
        
    presencas_atuais = {att.member_id: att.presente for att in evento.attendances}
    
    return render_template(
        'realizar_chamada.html', 
        evento=evento, 
        eventos=eventos,
        membros=membros, 
        presencas_atuais=presencas_atuais,
        departamentos=departamentos,
        departamento_filtro=departamento_filtro
    )