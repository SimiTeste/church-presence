import csv
from io import StringIO
from flask import Blueprint, render_template, Response, abort, request
from flask_login import login_required, current_user
from models.member import Member
from models.attendance import Event, Attendance

reports_bp = Blueprint("reports", __name__)

@reports_bp.route("/reports")
@login_required
def index():
    # 🔒 Bloqueia usuários comuns para garantir que apenas o MASTER veja os relatórios gerais
    if getattr(current_user, 'tipo', None) != 'MASTER':
        abort(403)

    departamento_selecionado = request.args.get('departamento')

    # Consulta base filtrando por ativos e opcionalmente por departamento
    query = Member.query.filter_by(ativo=True)
    if departamento_selecionado:
        query = query.filter_by(departamento=departamento_selecionado)
        
    members = query.all()
    total_ebds = Event.query.count()
    
    relatorio_membros = []
    for member in members:
        presencas = Attendance.query.filter_by(member_id=member.id).count()
        porcentagem = round((presencas / total_ebds) * 100, 1) if total_ebds > 0 else 0
        
        relatorio_membros.append({
            "nome": member.nome,
            "departamento": member.departamento,
            "foto": member.foto,
            "presencas": presencas,
            "total_ebds": total_ebds,
            "porcentagem": porcentagem
        })

    # Ordena do MAIOR para o MENOR número de presenças (Ranking)
    ranking_membros = sorted(relatorio_membros, key=lambda x: (x["presencas"], x["porcentagem"]), reverse=True)

    return render_template("reports.html", 
                           relatorio_membros=ranking_membros, 
                           departamento_selecionado=departamento_selecionado)

@reports_bp.route("/reports/export_csv")
@login_required
def export_csv():
    # 🔒 Bloqueia usuários comuns na exportação de dados sensíveis
    if getattr(current_user, 'tipo', None) != 'MASTER':
        abort(403)

    departamento_selecionado = request.args.get('departamento')

    si = StringIO()
    cw = csv.writer(si)
    
    # Cabeçalho do CSV
    cw.writerow(["Nome", "Departamento", "Presencas", "Total EBDs", "Assiduidade (%)"])
    
    query = Member.query.filter_by(ativo=True)
    if departamento_selecionado:
        query = query.filter_by(departamento=departamento_selecionado)
        
    members = query.order_by(Member.nome.asc()).all()
    total_ebds = Event.query.count()
    
    for member in members:
        presencas = Attendance.query.filter_by(member_id=member.id).count()
        porcentagem = round((presencas / total_ebds) * 100, 1) if total_ebds > 0 else 0
        cw.writerow([member.nome, member.departamento, presencas, total_ebds, f"{porcentagem}%"])
        
    output = si.getvalue()
    filename = f"relatorio_frequencia_{departamento_selecionado.lower()}.csv" if departamento_selecionado else "relatorio_frequencia_ebd.csv"
    
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename={filename}"}
    )