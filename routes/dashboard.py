from flask import Blueprint, render_template
from flask_login import login_required, current_user
from models import db
from models.member import Member
from models.attendance import Event, Attendance

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/dashboard")
@login_required
def index():
    # 🔒 Se não for MASTER, exibe o painel do usuário comum
    if getattr(current_user, 'tipo', None) != 'MASTER':
        
        # --- CORREÇÃO AQUI ---
        # Busca o membro real vinculado ao usuário logado (pelo CPF ou Nome)
        membro_vinculado = None
        if hasattr(current_user, 'cpf') and current_user.cpf:
            membro_vinculado = Member.query.filter_by(cpf=current_user.cpf).first()
            
        if not membro_vinculado:
            # Fallback: Se não achar por CPF, busca pelo nome
            membro_vinculado = Member.query.filter_by(nome=current_user.nome).first()
            
        # Se achou o membro, usa o ID real dele. Se não, usa o fallback.
        real_member_id = membro_vinculado.id if membro_vinculado else getattr(current_user, 'member_id', current_user.id)
        # ---------------------
        
        # 1. Busca as presenças individuais do usuário
        presencas_usuario = Attendance.query.filter_by(member_id=real_member_id).join(Event).order_by(Event.data.desc()).all()
        
        dias_comparecidos = []
        for p in presencas_usuario:
            if p.event:
                dias_comparecidos.append({
                    "nome_evento": p.event.nome,
                    "data": p.event.data.strftime("%d/%m/%Y")
                })

        total_presencas_usuario = len(dias_comparecidos)

        # --- NOVO: Cálculo de Faltas ---
        total_ebds_geral = Event.query.count()
        total_faltas_usuario = total_ebds_geral - total_presencas_usuario
        
        # Prevenção: garante que faltas não fiquem negativas caso haja erro de registro
        if total_faltas_usuario < 0:
            total_faltas_usuario = 0 
        # -------------------------------

        # 2. Calcula o Ranking Geral com Nomes e Departamentos
        ranking_dados = db.session.query(
            Member.id,
            Member.nome,
            Member.departamento, # <-- Busca o departamento
            db.func.count(Attendance.id).label('total')
        ).join(Attendance, Member.id == Attendance.member_id).group_by(Member.id).order_by(db.desc('total')).all()

        ranking_completo = []
        posicao_usuario = "-"
        
        for index, item in enumerate(ranking_dados, start=1):
            ranking_completo.append({
                "posicao": index,
                "nome": item.nome,
                "departamento": item.departamento if item.departamento else "-", # <-- Adiciona o departamento ao dicionário
                "total": item.total
            })
            # Usa o ID real corrigido para definir a posição no cartão
            if item.id == real_member_id:
                posicao_usuario = index

        return render_template(
            "dashboard_user.html", 
            user=current_user,
            dias_comparecidos=dias_comparecidos,
            total_presencas=total_presencas_usuario,
            total_faltas=total_faltas_usuario, # <-- Nova variável enviada para o Front-end
            posicao=posicao_usuario,
            ranking_completo=ranking_completo
        )

    # 👑 Se for MASTER, carrega os dados administrativos normais
    total_membros = Member.query.filter_by(ativo=True).count()
    total_ebds = Event.query.count()
    total_presencas = Attendance.query.count()
    
    media_presenca = round(total_presencas / total_ebds, 1) if total_ebds > 0 else 0

    ebds = Event.query.order_by(Event.data.desc()).limit(5).all()
    relatorio_rapido = []
    
    for ebd in ebds:
        qtd_presentes = Attendance.query.filter_by(event_id=ebd.id).count()
        relatorio_rapido.append({
            "nome": ebd.nome,
            "data": ebd.data.strftime("%d/%m/%Y"),
            "presentes": qtd_presentes
        })

    return render_template(
        "dashboard.html", 
        total_membros=total_membros, 
        total_ebds=total_ebds,
        media_presenca=media_presenca,
        relatorio_rapido=relatorio_rapido
    )