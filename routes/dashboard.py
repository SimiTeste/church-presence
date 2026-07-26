import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from models import db
from models.member import Member
from models.attendance import Event, Attendance
from models.notice import Notice

dashboard_bp = Blueprint("dashboard", __name__)

def get_daily_quote():
    quotes = [
        "Dedicação e constância transformam o aprendizado em sabedoria.",
        "Cada aula da EBD é uma semente plantada para o crescimento espiritual.",
        "A fidelidade nas pequenas coisas prepara você para grandes propósitos.",
        "Crescer em comunhão e conhecimento é o caminho para uma vida plena.",
        "Sua presença faz a diferença na nossa comunidade de fé.",
        "O conhecimento da Palavra ilumina os passos e fortalece a jornada.",
        "Construir um futuro sólido começa com o aprendizado diário."
    ]
    day_of_year = datetime.date.today().timetuple().tm_yday
    return quotes[day_of_year % len(quotes)]

@dashboard_bp.route("/dashboard")
@login_required
def index():
    frase_motivacional = get_daily_quote()

    avisos = []
    try:
        avisos = Notice.query.filter_by(ativo=True).order_by(Notice.data_criacao.desc()).all()
    except Exception:
        avisos = []

    user_tipo = getattr(current_user, 'tipo', None)

    # 1. 👑 Se for MASTER
    if user_tipo == 'MASTER':
        total_membros = Member.query.filter_by(ativo=True).count()
        total_ebds = Event.query.count()
        total_presencas = Attendance.query.filter_by(presente=True).count()
        
        media_presenca = round(total_presencas / total_ebds, 1) if total_ebds > 0 else 0

        ebds = Event.query.order_by(Event.data.desc()).limit(5).all()
        relatorio_rapido = []
        
        for ebd in ebds:
            qtd_presentes = Attendance.query.filter_by(event_id=ebd.id, presente=True).count()
            relatorio_rapido.append({
                "nome": ebd.nome,
                "data": ebd.data.strftime("%d/%m/%Y"),
                "presentes": qtd_presentes
            })

        try:
            todos_avisos = Notice.query.order_by(Notice.data_criacao.desc()).all()
        except Exception:
            todos_avisos = []

        return render_template(
            "dashboard.html", 
            total_membros=total_membros, 
            total_ebds=total_ebds,
            media_presenca=media_presenca,
            relatorio_rapido=relatorio_rapido,
            avisos=todos_avisos
        )

    # 2. 🛡️ Se for LÍDER
    if user_tipo == 'LIDER':
        total_membros = Member.query.filter_by(ativo=True).count()
        total_ebds = Event.query.count()
        total_presencas = Attendance.query.filter_by(presente=True).count()
        
        media_presenca = round(total_presencas / total_ebds, 1) if total_ebds > 0 else 0

        ebds = Event.query.order_by(Event.data.desc()).limit(5).all()
        relatorio_rapido = []
        
        for ebd in ebds:
            qtd_presentes = Attendance.query.filter_by(event_id=ebd.id, presente=True).count()
            relatorio_rapido.append({
                "nome": ebd.nome,
                "data": ebd.data.strftime("%d/%m/%Y"),
                "presentes": qtd_presentes
            })

        return render_template(
            "dashboard_lider.html", 
            total_membros=total_membros, 
            total_ebds=total_ebds,
            media_presenca=media_presenca,
            relatorio_rapido=relatorio_rapido,
            avisos=avisos
        )

    # 3. 👤 Se for usuário COMUM (USER)
    membro_vinculado = None
    if hasattr(current_user, 'cpf') and current_user.cpf:
        membro_vinculado = Member.query.filter_by(cpf=current_user.cpf).first()
        
    if not membro_vinculado:
        membro_vinculado = Member.query.filter_by(nome=current_user.nome).first()
        
    real_member_id = membro_vinculado.id if membro_vinculado else getattr(current_user, 'member_id', current_user.id)
    
    query_presencas_usuario = Attendance.query.filter_by(member_id=real_member_id, presente=True)
    presencas_usuario = query_presencas_usuario.join(Event).order_by(Event.data.desc()).all()
    
    dias_comparecidos = []
    for p in presencas_usuario:
        if p.event:
            dias_comparecidos.append({
                "nome_evento": p.event.nome,
                "data": p.event.data.strftime("%d/%m/%Y")
            })

    total_presencas_usuario = len(dias_comparecidos)
    total_ebds_geral = Event.query.count() or 0
    total_faltas_usuario = max(0, total_ebds_geral - total_presencas_usuario)

    # Garante que pega todos os membros (removendo o filtro restritivo caso haja registros mal formatados, ou trazendo todos onde ativo não seja explicitamente False)
    members_ativos = Member.query.filter((Member.ativo == True) | (Member.ativo == None)).all()
    
    lista_ranking = []
    for m in members_ativos:
        p_count = Attendance.query.filter_by(member_id=m.id, presente=True).count()
        porcentagem = round((p_count / total_ebds_geral) * 100, 1) if total_ebds_geral > 0 else 0
        
        lista_ranking.append({
            "member_id": m.id,
            "nome": m.nome,
            "departamento": m.departamento if m.departamento else "-",
            "total": p_count,
            "porcentagem": porcentagem
        })

    # Ordenação exata: 1º Presenças desc, 2º Porcentagem desc, 3º Nome A-Z
    lista_ranking.sort(key=lambda x: (-x["total"], -x["porcentagem"], x["nome"]))

    ranking_completo = []
    posicao_usuario = "-"
    
    for index, r in enumerate(lista_ranking, start=1):
        ranking_completo.append({
            "posicao": index,
            "nome": r["nome"],
            "departamento": r["departamento"],
            "total": r["total"]
        })
        if r["member_id"] == real_member_id:
            posicao_usuario = index

    return render_template(
        "dashboard_user.html", 
        user=current_user,
        dias_comparecidos=dias_comparecidos,
        total_presencas=total_presencas_usuario,
        total_faltas=total_faltas_usuario,
        posicao=posicao_usuario,
        ranking_completo=ranking_completo,
        frase_motivacional=frase_motivacional,
        avisos=avisos
    )


@dashboard_bp.route("/admin/avisos/novo", methods=["POST"])
@login_required
def criar_aviso():
    user_tipo = getattr(current_user, 'tipo', None)
    if user_tipo != 'MASTER' and user_tipo != 'LIDER':
        return abort(403)
    
    titulo = request.form.get("titulo")
    conteudo = request.form.get("conteudo")
    
    if titulo and conteudo:
        try:
            novo_aviso = Notice(titulo=titulo, conteudo=conteudo, ativo=True)
            db.session.add(novo_aviso)
            db.session.commit()
            flash("Aviso publicado com sucesso!", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao publicar aviso: {e}", "danger")
    else:
        flash("Preencha o título e o conteúdo do aviso.", "danger")
        
    return redirect(url_for("dashboard.index"))


@dashboard_bp.route("/admin/avisos/excluir/<int:id>", methods=["POST"])
@login_required
def excluir_aviso(id):
    user_tipo = getattr(current_user, 'tipo', None)
    if user_tipo != 'MASTER' and user_tipo != 'LIDER':
        return abort(403)
        
    try:
        aviso = Notice.query.get_or_404(id)
        db.session.delete(aviso)
        db.session.commit()
        flash("Aviso removido com sucesso!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao remover aviso: {e}", "danger")
    
    return redirect(url_for("dashboard.index"))