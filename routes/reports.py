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
        presencas = Attendance.query.filter_by(member_id=member.id).count()
        porcentagem = round((presencas / total_ebds) * 100, 1) if total_ebds > 0 else 0
        
        relatorio_membros.append({
            "nome": getattr(member, 'nome', 'Sem Nome'),
            "departamento": getattr(member, 'departamento', 'Geral'),
            "foto": getattr(member, 'foto', None),
            "presencas": presencas,
            "total_ebds": total_ebds,
            "porcentagem": porcentagem
        })

    # Ordena do maior para o menor número de presenças
    ranking_membros = sorted(relatorio_membros, key=lambda x: (x["presencas"], x["porcentagem"]), reverse=True)

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
        
    members = query.order_by(Member.nome.asc()).all()
    total_ebds = Event.query.count() or 0
    
    for member in members:
        presencas = Attendance.query.filter_by(member_id=member.id).count()
        porcentagem = round((presencas / total_ebds) * 100, 1) if total_ebds > 0 else 0
        cw.writerow([member.nome, member.departamento, presencas, total_ebds, f"{porcentagem}%"])
        
    output = si.getvalue()
    dept_suffix = f"_{departamento_selecionado.lower()}" if departamento_selecionado else ""
    filename = f"relatorio_frequencia{dept_suffix}.csv"
    
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename={filename}"}
    )