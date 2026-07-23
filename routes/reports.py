import csv
from io import StringIO
from flask import Blueprint, render_template, Response
from flask_login import login_required
from models.member import Member
from models.attendance import Event, Attendance

reports_bp = Blueprint("reports", __name__)

@reports_bp.route("/reports")
@login_required
def index():
    members = Member.query.filter_by(ativo=True).all()
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

    return render_template("reports.html", relatorio_membros=ranking_membros)

@reports_bp.route("/reports/export_csv")
@login_required
def export_csv():
    si = StringIO()
    cw = csv.writer(si)
    
    # Cabeçalho do CSV
    cw.writerow(["Nome", "Departamento", "Presencas", "Total EBDs", "Assiduidade (%)"])
    
    members = Member.query.filter_by(ativo=True).order_by(Member.nome.asc()).all()
    total_ebds = Event.query.count()
    
    for member in members:
        presencas = Attendance.query.filter_by(member_id=member.id).count()
        porcentagem = round((presencas / total_ebds) * 100, 1) if total_ebds > 0 else 0
        cw.writerow([member.nome, member.departamento, presencas, total_ebds, f"{porcentagem}%"])
        
    output = si.getvalue()
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=relatorio_frequencia_ebd.csv"}
    )