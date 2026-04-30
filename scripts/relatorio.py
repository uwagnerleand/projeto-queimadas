import pandas as pd
import os
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors


# =========================
# 📥 DADOS
# =========================
ranking = pd.read_csv("outputs/analise/ranking_municipios.csv")
anual_obidos = pd.read_csv("outputs/analise/anual_obidos.csv")

ranking.columns = ["municipio", "focos"]
ranking["municipio"] = ranking["municipio"].str.upper()

# =========================
# 🧠 TRATAMENTO
# =========================
top1 = ranking.iloc[0]

pos_obidos = ranking[ranking["municipio"] == "OBIDOS"].index
pos_obidos = int(pos_obidos[0]) + 1 if len(pos_obidos) > 0 else "Não identificado"

total_para = ranking["focos"].sum()

focos_obidos = ranking[ranking["municipio"] == "OBIDOS"]["focos"]
focos_obidos = int(focos_obidos.values[0]) if not focos_obidos.empty else 0

percentual = (focos_obidos / total_para) * 100 if total_para > 0 else 0

anual_obidos.columns = ["ano", "focos"]

if len(anual_obidos) >= 2:
    tendencia = "aumento" if anual_obidos["focos"].iloc[-1] > anual_obidos["focos"].iloc[-2] else "redução"
else:
    tendencia = "estável"

# =========================
# 📄 METADADOS
# =========================
data_geracao = datetime.now().strftime("%d/%m/%Y")

# =========================
# 🧾 TIMBRE (FUNDO A4)
# =========================
def adicionar_fundo(canvas, doc):
    width, height = A4

    if os.path.exists("assets/logo.png"):
        canvas.drawImage(
            "assets/logo.png",
            0, 0,
            width=width,
            height=height,
            mask='auto'
        )

    # paginação (remova se conflitar com seu timbre)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.black)
    canvas.drawRightString(width - 40, 20, f"Página {doc.page}")

# =========================
# 📄 DOCUMENTO
# =========================
os.makedirs("outputs/relatorios", exist_ok=True)

doc = SimpleDocTemplate(
    "outputs/relatorios/relatorio_oficial_obidos.pdf",
    pagesize=A4,
    topMargin=150,
    bottomMargin=110,
    leftMargin=50,
    rightMargin=50
)

styles = getSampleStyleSheet()

# garantir texto visível
styles["Normal"].textColor = colors.black
styles["Heading2"].textColor = colors.black
styles["Title"].textColor = colors.black

# =========================
# ⚙️ CONFIGURAÇÃO
# =========================
MUNICIPIO = "OBIDOS"
ESTADO = "PARA"

conteudo = []

# =========================
# 🟦 CAPA
# =========================
conteudo.append(Spacer(1, 140))

conteudo.append(Paragraph("PREFEITURA MUNICIPAL DE ÓBIDOS", styles["Title"]))
conteudo.append(Paragraph("Secretaria Municipal de Meio Ambiente", styles["Normal"]))
conteudo.append(Spacer(1, 30))

conteudo.append(Paragraph("RELATÓRIO TÉCNICO DE MONITORAMENTO DE QUEIMADAS", styles["Heading2"]))
conteudo.append(Spacer(1, 20))

conteudo.append(Paragraph("Município de Óbidos - Pará", styles["Normal"]))
conteudo.append(Spacer(1, 10))

conteudo.append(Paragraph(f"Data de geração: {data_geracao}", styles["Normal"]))

conteudo.append(PageBreak())

# =========================
# 1. INTRODUÇÃO
# =========================
conteudo.append(Paragraph("1. INTRODUÇÃO", styles["Heading2"]))
conteudo.append(Spacer(1, 10))

conteudo.append(Paragraph(
    "Este relatório apresenta a análise dos focos de calor registrados no município de Óbidos, "
    "com base em dados de monitoramento ambiental. O objetivo é subsidiar ações de controle, "
    "prevenção e gestão ambiental.",
    styles["Normal"]
))

conteudo.append(Paragraph(
    "Os dados foram obtidos por meio de sistemas de monitoramento de focos de calor e posteriormente "
    "tratados e analisados para suporte à tomada de decisão no âmbito da gestão ambiental municipal.",
    styles["Normal"]
))

conteudo.append(Spacer(1, 20))

# =========================
# 2. RESULTADOS
# =========================
conteudo.append(Paragraph("2. RESULTADOS GERAIS", styles["Heading2"]))
conteudo.append(Spacer(1, 10))

conteudo.append(Paragraph(
    f"O município com maior número de focos no estado foi {top1['municipio']}, "
    f"totalizando {int(top1['focos'])} registros.",
    styles["Normal"]
))

conteudo.append(Paragraph(
    f"O município de Óbidos ocupa a posição {pos_obidos} no ranking estadual.",
    styles["Normal"]
))

conteudo.append(Paragraph(
    f"A participação de Óbidos corresponde a {percentual:.2f}% do total estadual.",
    styles["Normal"]
))

conteudo.append(Spacer(1, 20))

# =========================
# 3. ANÁLISE TEMPORAL
# =========================
conteudo.append(Paragraph("3. ANÁLISE TEMPORAL", styles["Heading2"]))
conteudo.append(Spacer(1, 10))

conteudo.append(Paragraph(
    f"A tendência observada indica um cenário de {tendencia} na ocorrência de focos de calor, "
    f"podendo estar associada a fatores climáticos e atividades antrópicas.",
    styles["Normal"]
))

for _, row in anual_obidos.iterrows():
    conteudo.append(Paragraph(
        f"{int(row['ano'])}: {int(row['focos'])} focos registrados.",
        styles["Normal"]
    ))

conteudo.append(Spacer(1, 20))

# =========================
# 📊 4. ANÁLISE GRÁFICA (MULTI-ANO)
# =========================
conteudo.append(Paragraph("4. ANÁLISE GRÁFICA", styles["Heading2"]))
conteudo.append(Spacer(1, 10))

def add_img(caminho, legenda):
    if os.path.exists(caminho):
        conteudo.append(Paragraph(legenda, styles["Normal"]))
        conteudo.append(Image(caminho, width=450, height=250))
        conteudo.append(Spacer(1, 20))
    else:
        conteudo.append(Paragraph(f"[Imagem não disponível: {legenda}]", styles["Normal"]))
        conteudo.append(Spacer(1, 10))

# =========================
# 📅 GRÁFICOS GERAIS (VISÃO MACRO)
# =========================

add_img(
    "outputs/graficos/obidos_evolucao.png",
    "Figura 1 – Evolução temporal dos focos de calor em Óbidos."
)

add_img(
    "outputs/graficos/obidos_anual.png",
    "Figura 2 – Distribuição anual dos focos de calor em Óbidos."
)

add_img(
    "outputs/graficos/obidos_heatmap.png",
    "Figura 3 – Heatmap de queimadas (mês x ano) em Óbidos."
)

conteudo.append(PageBreak())

# =========================
# 📊 GRÁFICOS POR ANO (DETALHAMENTO)
# =========================

anos = sorted(anual_obidos["ano"].unique())

fig_num = 4

for ano in anos:

    conteudo.append(Paragraph(f"Análise detalhada – {ano}", styles["Heading2"]))
    conteudo.append(Spacer(1, 10))

    # Mensal
    add_img(
        f"outputs/graficos/obidos_mensal_{ano}.png",
        f"Figura {fig_num} – Distribuição mensal dos focos em Óbidos ({ano})."
    )
    fig_num += 1

    # Variação
    add_img(
        f"outputs/graficos/obidos_variacao_{ano}.png",
        f"Figura {fig_num} – Variação percentual mensal em Óbidos ({ano})."
    )
    fig_num += 1

    # Ranking do estado
    add_img(
        f"outputs/graficos/top10_{ano}.png",
        f"Figura {fig_num} – Top 10 municípios com focos de calor no Pará ({ano})."
    )
    fig_num += 1

    # Comparação com municípios
    add_img(
        f"outputs/graficos/comparacao_{ano}.png",
        f"Figura {fig_num} – Comparação entre municípios do Pará ({ano})."
    )
    fig_num += 1

    conteudo.append(PageBreak())

# =========================
# 5. CONCLUSÃO
# =========================
conteudo.append(Paragraph("5. CONCLUSÃO", styles["Heading2"]))
conteudo.append(Spacer(1, 10))

conteudo.append(Paragraph(
    "Os dados analisados demonstram que o município de Óbidos apresenta participação relevante "
    "no contexto estadual das queimadas. A distribuição temporal evidencia padrões sazonais, "
    "reforçando a necessidade de monitoramento contínuo.",
    styles["Normal"]
))

conteudo.append(Paragraph(
    "Recomenda-se o fortalecimento de ações de fiscalização, educação ambiental e planejamento "
    "territorial sustentável, especialmente nos períodos críticos.",
    styles["Normal"]
))

# =========================
# 💾 GERAR PDF
# =========================
doc.build(conteudo, onFirstPage=adicionar_fundo, onLaterPages=adicionar_fundo)

print("RELATÓRIO OFICIAL GERADO COM SUCESSO")