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
    if getattr(current_user, 'tipo', None) != 'MASTER':
        abort(403)

    departamento_selecionado = request.args.get('departamento')

    # Consulta base filtrando por membros ativos
    query = Member.query.filter_by(ativo=True)
    if departamento_selecionado and departamento_selecionado.strip():
        query = query.filter_by(departamento=departamento_selecionado)
        
    members = query.all()
    total_ebds = Event.query.count() or 0
    
    relatorio_membros = []
    for member in members:
        presencas = Attendance.query.filter_by(member_id=member.id, presente=True).count()
        porcentagem = round((presencas / total_ebds) * 100, 1) if total_ebds > 0 else 0
        
        relatorio_membros.append({
            "member_id": member.id,
            "nome": getattr(member, 'nome', 'Sem Nome'),
            "departamento": getattr(member, 'departamento', 'Geral'),
            "foto": getattr(member, 'foto', None),
            "presencas": presencas,
            "total_ebds": total_ebds,
            "porcentagem": porcentagem
        })

    # Ordenação padronizada: 1º Presenças (desc), 2º Porcentagem (desc), 3º ID do Membro (asc)
    ranking_membros = sorted(relatorio_membros, key=lambda x: (-x["presencas"], -x["porcentagem"], x["member_id"]))

    return render_template("reports.html", 
                           relatorio_membros=ranking_membros, 
                           departamento_selecionado=departamento_selecionado)

@reports_bp.route("/reports/export_csv")
@login_required
def export_csv():
    if getattr(current_user, 'tipo', None) != 'MASTER':
        abort(403)

    departamento_selecionado = request.args.get('departamento')

    si = StringIO()
    cw = csv.writer(si)
    
    cw.writerow(["Nome", "Departamento", "Presencas", "Total EBDs", "Assiduidade (%)"])
    
    query = Member.query.filter_by(ativo=True)
    if departamento_selecionado and departamento_selecionado.strip():
        query = query.filter_by(departamento=departamento_selecionado)
        
    members = query.all()
    total_ebds = Event.query.count() or 0
    
    # Coleta e calcula os dados para ordenar o CSV exatamente igual ao painel web
    dados_csv = []
    for member in members:
        presencas = Attendance.query.filter_by(member_id=member.id, presente=True).count()
        porcentagem = round((presencas / total_ebds) * 100, 1) if total_ebds > 0 else 0
        
        dados_csv.append({
            "member_id": member.id,
            "nome": member.nome,
            "departamento": member.departamento,
            "presencas": presencas,
            "porcentagem": porcentagem
        })

    # Aplica a mesma ordenação padrão do sistema
    dados_csv.sort(key=lambda x: (-x["presencas"], (-x["porcentagem"]), x["member_id"]))

    # Escreve as linhas ordenadas no CSV
    for item in dados_csv:
        cw.writerow([item["nome"], item["departamento"], item["presencas"], total_ebds, f"{item['porcentagem']}%"])
        
    output = si.getvalue()
    dept_suffix = f"_{departamento_selecionado.lower()}" if departamento_selecionado else ""
    filename = f"relatorio_frequencia{dept_suffix}.csv"
    
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename={filename}"}
    )