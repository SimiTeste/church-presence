from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db
from models.notice import Notice
from models.member import Member
from models.attendance import Event, Attendance
from sqlalchemy import func
import requests  # Importado para buscar o versículo via API externa

leader_bp = Blueprint('leader', __name__)

@leader_bp.route('/leader/dashboard')
@login_required
def dashboard():
    if not current_user.is_authenticated or current_user.tipo not in ["MASTER", "LIDER"]:
        flash('Acesso negado. Área restrita.', 'danger')
        return redirect(url_for('dashboard.index'))
        
    avisos = Notice.query.order_by(Notice.data_criacao.desc()).all()
    eventos = Event.query.all()
    
    # Total de EBDs cadastradas no sistema (mesma lógica usada no relatorio do Master)
    total_ebds = Event.query.count() or 0
    
    # Busca todos os membros ativos
    members = Member.query.filter_by(ativo=True).all()
    
    ranking_calculado = []
    for member in members:
        # Conta exatamente igual ao relatório do master (apenas onde presente=True)
        presencas = Attendance.query.filter_by(member_id=member.id, presente=True).count()
        porcentagem = round((presencas / total_ebds) * 100, 1) if total_ebds > 0 else 0
        
        ranking_calculado.append({
            "member": member,
            "presencas": presencas,
            "porcentagem": porcentagem
        })
    
    # Ordena por presenças, porcentagem e desempata pelo ID do membro (Ordem de cadastro)
    ranking_calculado.sort(key=lambda x: (-x["presencas"], -x["porcentagem"], x["member"].id))
    
    # Formata para o template do líder esperar (passando tuplas no formato [ (Member, total_presencas), ... ])
    ranking_membros = [(item["member"], item["presencas"]) for item in ranking_calculado]

    # === BUSCA DO VERSÍCULO DO DIA ===
    try:
        response = requests.get("https://bolsadepulgas.com.br/api/versiculo")
        if response.status_code == 200:
            dados_versiculo = response.json()
            versiculo_texto = dados_versiculo.get('text', 'O Senhor é o meu pastor; nada me faltará.')
            versiculo_referencia = dados_versiculo.get('reference', 'Salmos 23:1')
        else:
            versiculo_texto = "O Senhor é o meu pastor; nada me faltará."
            versiculo_referencia = "Salmos 23:1"
    except Exception:
        versiculo_texto = "O Senhor é o meu pastor; nada me faltará."
        versiculo_referencia = "Salmos 23:1"

    return render_template(
        'dashboard_lider.html', 
        avisos=avisos, 
        eventos=eventos, 
        ranking_membros=ranking_membros,
        versiculo_texto=versiculo_texto,
        versiculo_referencia=versiculo_referencia
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
        for membro in membros:
            nome_campo = f'presente_{membro.id}'
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
    
    # === CONTAGEM CORRIGIDA PARA O FILTRO ===
    # Conta apenas os presentes que pertencem aos membros listados na tela (respeitando o filtro)
    total_presentes_filtrados = sum(1 for m in membros if presencas_atuais.get(m.id, False))
    
    return render_template(
        'realizar_chamada.html', 
        evento=evento, 
        eventos=eventos,
        membros=membros, 
        presencas_atuais=presencas_atuais,
        departamentos=departamentos,
        departamento_filtro=departamento_filtro,
        total_presentes_filtrados=total_presentes_filtrados
    )