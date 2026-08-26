"""
Módulo de Geração Automatizada de Relatórios Técnicos em PDF.

Produz documento técnico oficial formatado (padrão A4) com capa,
introdução, estatísticas descritivas, análise de tendências,
inserção dinâmica de gráficos técnicos e recomendações ambientais.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from datetime import datetime
from typing import List, Optional

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("queimadas.relatorio")


def adicionar_fundo(canvas, doc, logo_path: Optional[str] = "assets/logo.png") -> None:
    """Aplica o timbre de fundo A4 e a paginação original do modelo de relatório."""
    width, height = A4

    if logo_path and os.path.exists(logo_path):
        try:
            canvas.drawImage(
                logo_path,
                0,
                0,
                width=width,
                height=height,
                mask="auto",
            )
        except Exception as err:
            logger.warning("Não foi possível renderizar imagem de fundo: %s", err)

    # Paginação padrão do modelo manual
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.black)
    canvas.drawRightString(width - 40, 20, f"Página {doc.page}")


def gerar_relatorio_pdf(
    caminho_ranking: str = "outputs/analise/ranking_municipios.csv",
    caminho_anual: str = "outputs/analise/anual_obidos.csv",
    diretorio_graficos: str = "outputs/graficos",
    caminho_saida_pdf: str = "outputs/relatorios/relatorio_oficial_obidos.pdf",
    municipio: str = "OBIDOS",
    estado: str = "PARA",
    orgao_emissor: str = "Secretaria Municipal de Meio Ambiente",
    logo_path: str = "assets/logo.png",
) -> str:
    """Compila o relatório técnico oficial no modelo padronizado da Prefeitura de Óbidos."""
    os.makedirs(os.path.dirname(caminho_saida_pdf) or ".", exist_ok=True)

    # 1. Carregar dados de ranking
    if not os.path.exists(caminho_ranking):
        raise FileNotFoundError(f"Arquivo de ranking não encontrado: {caminho_ranking}")

    ranking = pd.read_csv(caminho_ranking)
    ranking.columns = ["municipio", "focos"]
    ranking["municipio"] = ranking["municipio"].astype(str).str.upper().str.strip()

    # 2. Carregar dados anuais
    if os.path.exists(caminho_anual):
        anual_obidos = pd.read_csv(caminho_anual)
        anual_obidos.columns = ["ano", "focos"]
    else:
        anual_obidos = pd.DataFrame(columns=["ano", "focos"])

    # 3. Tratamento estatístico
    top1 = ranking.iloc[0] if not ranking.empty else {"municipio": "N/A", "focos": 0}
    pos_match = ranking[ranking["municipio"] == municipio.upper()].index
    pos_obidos = int(pos_match[0]) + 1 if len(pos_match) > 0 else "Não identificado"

    total_para = ranking["focos"].sum()
    focos_obidos_match = ranking[ranking["municipio"] == municipio.upper()]["focos"]
    focos_obidos = int(focos_obidos_match.values[0]) if not focos_obidos_match.empty else 0
    percentual = (focos_obidos / total_para * 100) if total_para > 0 else 0.0

    if len(anual_obidos) >= 2:
        tendencia = (
            "aumento"
            if anual_obidos["focos"].iloc[-1] > anual_obidos["focos"].iloc[-2]
            else "redução"
        )
    else:
        tendencia = "estável"

    data_geracao = datetime.now().strftime("%d/%m/%Y")

    # Documento PDF configurado com as margens oficiais do modelo manual
    doc = SimpleDocTemplate(
        caminho_saida_pdf,
        pagesize=A4,
        topMargin=150,
        bottomMargin=110,
        leftMargin=50,
        rightMargin=50,
    )

    styles = getSampleStyleSheet()

    # Garantir texto 100% visível em preto puro
    styles["Normal"].textColor = colors.black
    styles["Normal"].fontSize = 10
    styles["Normal"].leading = 14
    styles["Normal"].fontName = "Helvetica"

    styles["Heading2"].textColor = colors.black
    styles["Heading2"].fontSize = 13
    styles["Heading2"].leading = 17
    styles["Heading2"].fontName = "Helvetica-Bold"
    styles["Heading2"].spaceBefore = 12
    styles["Heading2"].spaceAfter = 8

    styles["Title"].textColor = colors.black
    styles["Title"].fontSize = 18
    styles["Title"].leading = 22
    styles["Title"].fontName = "Helvetica-Bold"

    conteudo: List[object] = []

    # =========================
    # 🟦 CAPA (MODELO ORIGINAL)
    # =========================
    conteudo.append(Spacer(1, 140))
    conteudo.append(Paragraph(f"PREFEITURA MUNICIPAL DE {municipio.upper()}", styles["Title"]))
    conteudo.append(Spacer(1, 8))
    conteudo.append(Paragraph(orgao_emissor, styles["Normal"]))
    conteudo.append(Spacer(1, 30))

    conteudo.append(Paragraph("RELATÓRIO TÉCNICO DE MONITORAMENTO DE QUEIMADAS", styles["Heading2"]))
    conteudo.append(Spacer(1, 20))

    conteudo.append(Paragraph(f"Município de {municipio.title()} - {estado.title()}", styles["Normal"]))
    conteudo.append(Spacer(1, 10))

    conteudo.append(Paragraph(f"Data de geração: {data_geracao}", styles["Normal"]))
    conteudo.append(PageBreak())

    # =========================
    # 1. INTRODUÇÃO
    # =========================
    conteudo.append(Paragraph("1. INTRODUÇÃO", styles["Heading2"]))
    conteudo.append(Spacer(1, 10))

    conteudo.append(
        Paragraph(
            f"Este relatório apresenta a análise dos focos de calor registrados no município de {municipio.title()}, "
            f"com base em dados de monitoramento ambiental. O objetivo é subsidiar ações de controle, "
            f"prevenção e gestão ambiental.",
            styles["Normal"],
        )
    )
    conteudo.append(Spacer(1, 8))
    conteudo.append(
        Paragraph(
            "Os dados foram obtidos por meio de sistemas de monitoramento de focos de calor e posteriormente "
            "tratados e analisados para suporte à tomada de decisão no âmbito da gestão ambiental municipal.",
            styles["Normal"],
        )
    )
    conteudo.append(Spacer(1, 20))

    # =========================
    # 2. RESULTADOS GERAIS & TABELA MENSAL
    # =========================
    conteudo.append(Paragraph("2. RESULTADOS GERAIS E DISTRIBUIÇÃO MENSAL", styles["Heading2"]))
    conteudo.append(Spacer(1, 6))

    conteudo.append(
        Paragraph(
            f"No consolidado estadual, o município com maior número de focos foi <b>{top1['municipio']}</b>, "
            f"totalizando <b>{int(top1['focos']):,}</b> registros.",
            styles["Normal"],
        )
    )
    conteudo.append(Spacer(1, 4))
    conteudo.append(
        Paragraph(
            f"O município de {municipio.title()} ocupa a posição <b>#{pos_obidos}</b> no ranking estadual, "
            f"com <b>{focos_obidos:,}</b> focos registrados ({percentual:.2f}% do total do Estado do {estado.title()}).",
            styles["Normal"],
        )
    )
    conteudo.append(Spacer(1, 8))

    # Tabela 01: Matriz Mensal (Janeiro a Dezembro + Total)
    caminho_para = "dados/tratado/para.csv"
    if os.path.exists(caminho_para):
        try:
            df_p = pd.read_csv(caminho_para, low_memory=False)
            df_ob = df_p[df_p["municipio"] == municipio.upper()].copy()
            df_ob["data"] = pd.to_datetime(df_ob["data"], errors="coerce")
            df_ob["ano"] = df_ob["data"].dt.year.astype(int)
            df_ob["mes"] = df_ob["data"].dt.month.astype(int)

            piv_m = df_ob.pivot_table(index="ano", columns="mes", values="latitude", aggfunc="count", fill_value=0)
            for m_num in range(1, 13):
                if m_num not in piv_m.columns:
                    piv_m[m_num] = 0
            piv_m = piv_m[[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]]
            piv_m["Total"] = piv_m.sum(axis=1)

            t1_data = [["Ano", "Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez", "Total"]]
            for yr, row_m in piv_m.iterrows():
                t1_data.append([str(yr)] + [str(int(v)) for v in row_m.values])

            t1_table = Table(t1_data, colWidths=[35] + [33]*12 + [40])
            t1_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 7.5),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#64748b")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 1), (-1, -1), 7.5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
            ]))
            conteudo.append(Paragraph("<b>Tabela 01: Quantitativo mensal de focos de queimadas em Óbidos (2020 a 2026)</b>", styles["Normal"]))
            conteudo.append(Spacer(1, 4))
            conteudo.append(t1_table)
            conteudo.append(Spacer(1, 14))
        except Exception as e:
            logger.warning("Erro ao gerar tabela mensal: %s", e)

    # =========================
    # 3. MUNICÍPIOS EXTREMANTES / LIMÍTROFES
    # =========================
    conteudo.append(Paragraph("3. COMPARAÇÃO COM MUNICÍPIOS EXTREMANTES (CALHA NORTE / BAIXO AMAZONAS)", styles["Heading2"]))
    conteudo.append(Spacer(1, 6))

    if os.path.exists(caminho_para):
        try:
            extremantes = ["OBIDOS", "ALENQUER", "ALMEIRIM", "CURUA", "JURUTI", "ORIXIMINA", "SANTAREM"]
            df_ext = df_p[df_p["municipio"].isin(extremantes)].copy()
            df_ext["data"] = pd.to_datetime(df_ext["data"], errors="coerce")
            df_ext["ano"] = df_ext["data"].dt.year.astype(int)
            piv_ext = df_ext.pivot_table(index="municipio", columns="ano", values="latitude", aggfunc="count", fill_value=0)
            
            anos_ext = sorted(piv_ext.columns)
            t2_data = [["Município"] + [str(a) for a in anos_ext] + ["Total"]]
            for mun_name, r_ext in piv_ext.iterrows():
                total_mun_ext = int(r_ext.sum())
                t2_data.append([mun_name.title()] + [str(int(v)) for v in r_ext.values] + [str(total_mun_ext)])

            t2_table = Table(t2_data, colWidths=[110] + [48]*len(anos_ext) + [55])
            t2_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 8),
                ("ALIGN", (1, 0), (-1, -1), "CENTER"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#64748b")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 1), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
                ("TOPPADDING", (0, 0), (-1, -1), 3.5),
            ]))
            conteudo.append(Paragraph("<b>Tabela 02: Focos de queimadas nos municípios extremantes e limítrofes (2020 a 2026)</b>", styles["Normal"]))
            conteudo.append(Spacer(1, 4))
            conteudo.append(t2_table)
            conteudo.append(Spacer(1, 14))
        except Exception as e:
            logger.warning("Erro ao gerar tabela de extremantes: %s", e)

    conteudo.append(PageBreak())

    # =========================
    # 4. ANÁLISE TERRITORIAL EM ÓBIDOS (27 TERRITÓRIOS OFICIAIS)
    # =========================
    conteudo.append(Paragraph("4. ANÁLISE TERRITORIAL EM ÓBIDOS: ASSENTAMENTOS, QUILOMBOLAS, UCs E ÁREAS INDÍGENAS", styles["Heading2"]))
    conteudo.append(Spacer(1, 6))

    conteudo.append(
        Paragraph(
            "Estratificação espacial nos 27 territórios da divisão administrativa de Óbidos (T.D.A), "
            "compreendendo Projetos de Assentamento (INCRA/PAEs), Áreas Quilombolas (PAQs), Terras Indígenas (TIs) "
            "e Unidades de Conservação (UCs):",
            styles["Normal"],
        )
    )
    conteudo.append(Spacer(1, 8))

    # Tabela 03: Categorias Territoriais
    caminho_cat_csv = "outputs/analise/territorios_categorias_obidos.csv"
    if os.path.exists(caminho_cat_csv):
        df_cat_rel = pd.read_csv(caminho_cat_csv)
        dados_tabela_cat = [["Categoria Territorial", "Total de Focos", "Participação (%)"]]
        for _, row in df_cat_rel.iterrows():
            dados_tabela_cat.append([
                str(row["categoria_territorial"]),
                f"{int(row['total_focos']):,}".replace(",", "."),
                f"{float(row['percentual_%']):.2f}%",
            ])

        t_cat = Table(dados_tabela_cat, colWidths=[240, 110, 110])
        t_cat.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 8.5),
            ("ALIGN", (1, 0), (-1, -1), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#64748b")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f1f5f9")]),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 1), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
        ]))
        conteudo.append(Paragraph("<b>Tabela 03: Resumo por Categoria Territorial em Óbidos (2020 a 2026)</b>", styles["Normal"]))
        conteudo.append(Spacer(1, 4))
        conteudo.append(t_cat)
        conteudo.append(Spacer(1, 12))

    # Tabela 04: Territórios Indígenas (Tumucumaque e Zoe)
    caminho_ti_csv = "outputs/analise/terras_indigenas_obidos.csv"
    if os.path.exists(caminho_ti_csv):
        df_ti_rel = pd.read_csv(caminho_ti_csv)
        col_nome = "nome_territorio" if "nome_territorio" in df_ti_rel.columns else df_ti_rel.columns[0]
        cols_ti = [c for c in df_ti_rel.columns if c != col_nome]
        dados_ti = [["Terra Indígena"] + cols_ti]
        for _, row in df_ti_rel.iterrows():
            dados_ti.append([str(row[col_nome])] + [str(int(row[c])) for c in cols_ti])
        
        t_ti = Table(dados_ti, colWidths=[180] + [38]*len(cols_ti))
        t_ti.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 8),
            ("ALIGN", (1, 0), (-1, -1), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#64748b")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f1f5f9")]),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 1), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
        ]))
        conteudo.append(Paragraph("<b>Tabela 04: Queimadas em Territórios Indígenas de Óbidos (2020 a 2026)</b>", styles["Normal"]))
        conteudo.append(Spacer(1, 4))
        conteudo.append(t_ti)
        conteudo.append(Spacer(1, 14))

    # Helper para adicionar imagens
    def add_img(caminho: str, legenda: str) -> None:
        if os.path.exists(caminho):
            conteudo.append(Paragraph(f"<b>{legenda}</b>", styles["Normal"]))
            conteudo.append(Spacer(1, 4))
            conteudo.append(Image(caminho, width=450, height=225))
            conteudo.append(Spacer(1, 14))
        else:
            conteudo.append(Paragraph(f"[Imagem não disponível: {legenda}]", styles["Normal"]))
            conteudo.append(Spacer(1, 10))

    add_img(
        "outputs/graficos/obidos_territorios_barras.png",
        "Figura 1 – Distribuição de focos por categoria territorial em Óbidos.",
    )
    add_img(
        "outputs/graficos/obidos_territorios_pizza.png",
        "Figura 2 – Proporção relativa de queimadas por categoria fundiária.",
    )
    conteudo.append(PageBreak())

    # =========================
    # 5. ANÁLISE GRÁFICA (MULTI-ANO & POR ANO)
    # =========================
    conteudo.append(Paragraph("5. ANÁLISE GRÁFICA", styles["Heading2"]))
    conteudo.append(Spacer(1, 10))

    # Gráficos gerais (Visão Macro)
    add_img(
        "outputs/graficos/obidos_evolucao.png",
        "Figura 3 – Evolução temporal dos focos de calor em Óbidos (2020 a 2026).",
    )

    add_img(
        "outputs/graficos/obidos_anual.png",
        "Figura 4 – Distribuição anual dos focos de calor em Óbidos.",
    )

    add_img(
        "outputs/graficos/obidos_heatmap.png",
        "Figura 5 – Heatmap de queimadas (mês x ano) em Óbidos.",
    )

    conteudo.append(PageBreak())

    # Gráficos por ano (Detalhamento 2020 a 2026)
    if not anual_obidos.empty:
        anos = sorted(anual_obidos["ano"].unique())
        fig_num = 6

        for ano in anos:
            ano_int = int(ano)
            conteudo.append(Paragraph(f"Análise detalhada – Ano {ano_int}", styles["Heading2"]))
            conteudo.append(Spacer(1, 10))

            # Mensal
            add_img(
                f"outputs/graficos/obidos_mensal_{ano_int}.png",
                f"Figura {fig_num} – Distribuição mensal dos focos em Óbidos ({ano_int}).",
            )
            fig_num += 1

            # Variação
            add_img(
                f"outputs/graficos/obidos_variacao_{ano_int}.png",
                f"Figura {fig_num} – Variação percentual mensal em Óbidos ({ano_int}).",
            )
            fig_num += 1

            # Top 10 estado
            add_img(
                f"outputs/graficos/top10_{ano_int}.png",
                f"Figura {fig_num} – Top 10 municípios com focos de calor no Pará ({ano_int}).",
            )
            fig_num += 1

            # Comparação
            add_img(
                f"outputs/graficos/comparacao_{ano_int}.png",
                f"Figura {fig_num} – Comparação entre municípios do Pará ({ano_int}).",
            )
            fig_num += 1

            conteudo.append(PageBreak())

    # =========================
    # 6. CONCLUSÃO
    # =========================
    conteudo.append(Paragraph("6. CONCLUSÃO", styles["Heading2"]))
    conteudo.append(Spacer(1, 10))

    conteudo.append(
        Paragraph(
            f"Os dados analisados demonstram que o município de {municipio.title()} apresenta participação relevante "
            f"no contexto estadual das queimadas. A distribuição temporal evidencia padrões sazonais bem definidos, "
            f"reforçando a necessidade de monitoramento contínuo.",
            styles["Normal"],
        )
    )
    conteudo.append(Spacer(1, 8))
    conteudo.append(
        Paragraph(
            "Recomenda-se o fortalecimento de ações de fiscalização, educação ambiental e planejamento "
            "territorial sustentável, especialmente nos períodos críticos de estiagem na região da Calha Norte.",
            styles["Normal"],
        )
    )

    # =========================
    # 💾 GERAR PDF
    # =========================
    doc.build(
        conteudo,
        onFirstPage=lambda c, d: adicionar_fundo(c, d, logo_path),
        onLaterPages=lambda c, d: adicionar_fundo(c, d, logo_path),
    )

    logger.info("Relatório PDF oficial gerado com sucesso: %s", caminho_saida_pdf)
    return caminho_saida_pdf


def parse_args() -> argparse.Namespace:
    """Configura argumentos de linha de comando."""
    parser = argparse.ArgumentParser(
        description="Gera relatório técnico em PDF de monitoramento de queimadas."
    )
    parser.add_argument(
        "--ranking",
        default="outputs/analise/ranking_municipios.csv",
        help="Caminho do CSV de ranking.",
    )
    parser.add_argument(
        "--anual", default="outputs/analise/anual_obidos.csv", help="Caminho do CSV anual."
    )
    parser.add_argument(
        "--graficos-dir", default="outputs/graficos", help="Pasta com os gráficos PNG."
    )
    parser.add_argument(
        "--saida-pdf",
        default="outputs/relatorios/relatorio_oficial_obidos.pdf",
        help="Caminho do PDF de saída.",
    )
    parser.add_argument("--municipio", default="OBIDOS", help="Município em análise.")
    parser.add_argument("--estado", default="PARA", help="Estado em análise.")
    return parser.parse_args()


def main() -> None:
    """Ponto de entrada do script."""
    args = parse_args()
    try:
        gerar_relatorio_pdf(
            caminho_ranking=args.ranking,
            caminho_anual=args.anual,
            diretorio_graficos=args.graficos_dir,
            caminho_saida_pdf=args.saida_pdf,
            municipio=args.municipio,
            estado=args.estado,
        )
    except Exception as exc:
        logger.error("Erro ao gerar relatório em PDF: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
