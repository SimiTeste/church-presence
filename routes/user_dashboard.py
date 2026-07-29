import datetime
from flask import Blueprint, render_template, abort, flash
from flask_login import login_required, current_user
from models.member import Member
from models.attendance import Event, Attendance
try:
    from models.notice import Notice
except ImportError:
    Notice = None

user_dashboard_bp = Blueprint("user_dashboard", __name__)

def get_daily_verse():
    versiculos = [
        {
            "texto": "Lâmpada para os meus pés é a tua palavra, e luz para o meu caminho.",
            "referencia": "Salmos 119:105"
        },
        {
            "texto": "Confie no Senhor de todo o coração e não se apoie em sua própria inteligência.",
            "referencia": "Provérbios 3:5"
        },
        {
            "texto": "O Senhor é o meu pastor; de nada terei falta.",
            "referencia": "Salmos 23:1"
        },
        {
            "texto": "Tudo posso naquele que me fortalece.",
            "referencia": "Filipenses 4:13"
        },
        {
            "texto": "Entrega o teu caminho ao Senhor; confia nele, e ele o fará.",
            "referencia": "Salmos 37:5"
        },
        {
            "texto": "O Senhor é a minha luz e a minha salvação; a quem temerei?",
            "referencia": "Salmos 27:1"
        },
        {
            "texto": "Busquem, primeiro, o reino de Deus e a sua justiça, e todas essas coisas lhes serão acrescentadas.",
            "referencia": "Mateus 6:33"
        }
    ]
    day_of_year = datetime.date.today().timetuple().tm_yday
    return versiculos[day_of_year % len(versiculos)]

@user_dashboard_bp.route("/user/dashboard")
@login_required
def index():
    # Garante que administradores/master usam o painel administrativo dedicado
    if getattr(current_user, 'tipo', None) == 'MASTER':
        return abort(403)

    versiculo_do_dia = get_daily_verse()

    # Busca os avisos ativos de forma segura caso a tabela ainda esteja se sincronizando
    avisos = []
    if Notice:
        try:
            avisos = Notice.query.filter_by(ativo=True).order_by(Notice.data_criacao.desc()).all()
        except Exception:
            avisos = []

    # Tenta encontrar o membro vinculado pelo CPF do usuário logado
    membro = Member.query.filter_by(cpf=current_user.cpf).first()

    total_ebds = Event.query.count() or 0
    
    # --- VERIFICAÇÃO DO ÚLTIMO DOMINGO (NOTIFICAÇÃO ESTILO APP) ---
    if membro:
        # Pega o último evento cadastrado (mais recente)
        ultimo_evento = Event.query.order_by(Event.data.desc(), Event.id.desc()).first()
        if ultimo_evento:
            att_ultimo = Attendance.query.filter_by(event_id=ultimo_evento.id, member_id=membro.id).first()
            foi_presente = False
            if att_ultimo:
                if hasattr(att_ultimo, 'presente'):
                    foi_presente = att_ultimo.presente
                else:
                    foi_presente = True

            # Dispara a mensagem flash correspondente
            if foi_presente:
                flash("Parabéns! Que bom ter você na EBD do último domingo, você é incrível! 🌟", "app-success")
            else:
                flash("Sentimos sua falta na EBD do último domingo! Esperamos você na próxima. 💙", "app-warning")
    # -------------------------------------------------------------

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
            versiculo_texto=versiculo_do_dia["texto"],
            versiculo_referencia=versiculo_do_dia["referencia"],
            avisos=avisos
        )

    # Busca presenças reais do membro (somente onde presente=True)
    query_presencas = Attendance.query.filter_by(member_id=membro.id)
    if hasattr(Attendance, 'presente'):
        presencas_membro = [p for p in query_presencas.all() if getattr(p, 'presente', True)]
    else:
        presencas_membro = query_presencas.all()
        
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

    # Calcula o ranking geral de todos os membros ativos usando a mesma regra dos demais painéis
    members_ativos = Member.query.filter_by(ativo=True).all()
    lista_ranking = []
    for m in members_ativos:
        q_p = Attendance.query.filter_by(member_id=m.id)
        if hasattr(Attendance, 'presente'):
            p_count = len([p for p in q_p.all() if getattr(p, 'presente', True)])
        else:
            p_count = q_p.count()
            
        porcentagem = round((p_count / total_ebds) * 100, 1) if total_ebds > 0 else 0
            
        lista_ranking.append({
            "member_id": m.id,
            "nome": m.nome,
            "departamento": m.departamento or "Geral",
            "total": p_count,
            "porcentagem": porcentagem
        })

    # Ordenação padronizada: 1º Presenças (desc), 2º Porcentagem (desc), 3º ID do Membro (asc)
    lista_ranking.sort(key=lambda x: (-x["total"], -x["porcentagem"], x["member_id"]))

    ranking_completo = []
    posicao_usuario = "-"
    for idx, r in enumerate(lista_ranking, start=1):
        if r["member_id"] == membro.id:
            posicao_usuario = idx
        ranking_completo.append({
            "posicao": idx,
            "nome": r["nome"],
            "departamento": r["departamento"],
            "total": r["total"],
            "porcentagem": f"{r['porcentagem']}%"
        })

    return render_template(
        "dashboard_user.html",
        user=current_user,
        posicao=posicao_usuario,
        total_presencas=total_presencas,
        total_faltas=total_faltas,
        dias_comparecidos=dias_comparecidos,
        ranking_completo=ranking_completo,
        versiculo_texto=versiculo_do_dia["texto"],
        versiculo_referencia=versiculo_do_dia["referencia"],
        avisos=avisos
    )