import datetime
from flask import Blueprint, render_template, abort
from flask_login import login_required, current_user
from models.member import Member
from models.attendance import Event, Attendance
try:
    from models.notice import Notice
except ImportError:
    Notice = None

user_dashboard_bp = Blueprint("user_dashboard", __name__)

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

@user_dashboard_bp.route("/user/dashboard")
@login_required
def index():
    # Garante que administradores/master usam o painel administrativo dedicado
    if getattr(current_user, 'tipo', None) == 'MASTER':
        return abort(403)

    frase_motivacional = get_daily_quote()

    # Busca os avisos ativos de forma segura caso a tabela ainda esteja se sincronizando
    avisos = []
    if Notice:
        try:
            avisos = Notice.query.filter_by(ativo=True).order_by(Notice.data_criacao.desc()).all()
        except Exception:
            avisos = []

    # Tenta encontrar o membro vinculado pelo CPF do usuário logado
    membro = Member.query.filter_by(cpf=current_user.cpf).first()

    total_ebds = Event.query.count()
    
    # Se o membro não estiver cadastrado na tabela Member ainda, inicializa com valores zerados
    if not membro:
        return render_template(
            "dashboard_user.html",
            user=current_user,
            posicao="-",
            total_presencas=0,
            total_faltas=total_ebds,
            dias_comparecidos=[],
            ranking_completo=[],
            frase_motivacional=frase_motivacional,
            avisos=avisos
        )

    # Busca presenças do membro
    presencas_membro = Attendance.query.filter_by(member_id=membro.id).all()
    total_presencas = len(presencas_membro)
    total_faltas = max(0, total_ebds - total_presencas)

    dias_comparecidos = []
    for p in presencas_membro:
        evento = Event.query.get(p.event_id)
        if evento:
            dias_comparecidos.append({
                "data": evento.data.strftime('%d/%m/%Y'),
                "nome_evento": evento.nome
            })

    # Calcula o ranking geral de todos os membros ativos para exibir na tabela
    members_ativos = Member.query.filter_by(ativo=True).all()
    lista_ranking = []
    for m in members_ativos:
        p_count = Attendance.query.filter_by(member_id=m.id).count()
        lista_ranking.append({
            "nome": m.nome,
            "departamento": m.departamento or "Geral",
            "total": p_count
        })

    # Ordena do maior para o menor número de presenças
    lista_ranking = sorted(lista_ranking, key=lambda x: x["total"], reverse=True)

    ranking_completo = []
    posicao_usuario = "-"
    for idx, r in enumerate(lista_ranking, start=1):
        if r["nome"] == membro.nome:
            posicao_usuario = idx
        ranking_completo.append({
            "posicao": idx,
            "nome": r["nome"],
            "departamento": r["departamento"],
            "total": r["total"]
        })

    return render_template(
        "dashboard_user.html",
        user=current_user,
        posicao=posicao_usuario,
        total_presencas=total_presencas,
        total_faltas=total_faltas,
        dias_comparecidos=dias_comparecidos,
        ranking_completo=ranking_completo,
        frase_motivacional=frase_motivacional,
        avisos=avisos
    )