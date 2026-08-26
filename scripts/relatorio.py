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


def adicionar_fundo_e_paginacao(canvas, doc, logo_path: Optional[str] = None) -> None:
    """Aplica o timbre de cabeçalho e a numeração de páginas no documento PDF."""
    width, height = A4

    if logo_path and os.path.exists(logo_path):
        try:
            canvas.drawImage(logo_path, 0, 0, width=width, height=height, mask="auto")
        except Exception as err:
            logger.warning("Não foi possível renderizar imagem de fundo: %s", err)

    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#64748b"))
    canvas.drawRightString(width - 40, 20, f"Página {doc.page} | Monitoramento Queimadas")
    canvas.drawString(40, 20, "Documento gerado automaticamente pelo Sistema de Análise")


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
    """Compila dados e imagens geradas em um relatório técnico oficial em PDF.

    Args:
        caminho_ranking: Caminho do CSV de ranking de municípios.
        caminho_anual: Caminho do CSV de histórico anual.
        diretorio_graficos: Pasta onde os PNGs dos gráficos estão armazenados.
        caminho_saida_pdf: Caminho completo para gravação do PDF.
        municipio: Nome do município em foco.
        estado: Nome do estado em foco.
        orgao_emissor: Nome da entidade governamental ou órgão emissor.
        logo_path: Caminho para logotipo ou papel timbrado.

    Returns:
        Caminho do arquivo PDF gerado.
    """
    os.makedirs(os.path.dirname(caminho_saida_pdf) or ".", exist_ok=True)

    # Carregar dados
    if not os.path.exists(caminho_ranking):
        raise FileNotFoundError(f"Arquivo de ranking não encontrado: {caminho_ranking}")

    ranking = pd.read_csv(caminho_ranking)
    ranking.columns = ["municipio", "focos"]
    ranking["municipio"] = ranking["municipio"].astype(str).str.upper().str.strip()

    if os.path.exists(caminho_anual):
        anual = pd.read_csv(caminho_anual)
        anual.columns = ["ano", "focos"]
    else:
        anual = pd.DataFrame(columns=["ano", "focos"])

    # Cálculos analíticos
    top1 = ranking.iloc[0] if not ranking.empty else {"municipio": "N/A", "focos": 0}
    pos_match = ranking[ranking["municipio"] == municipio.upper()].index
    pos_municipio = int(pos_match[0]) + 1 if len(pos_match) > 0 else "Não identificado"

    total_estado = ranking["focos"].sum()
    focos_mun_match = ranking[ranking["municipio"] == municipio.upper()]["focos"]
    focos_mun = int(focos_mun_match.values[0]) if not focos_mun_match.empty else 0
    percentual = (focos_mun / total_estado * 100) if total_estado > 0 else 0.0

    if len(anual) >= 2:
        tendencia = "aumento" if anual["focos"].iloc[-1] > anual["focos"].iloc[-2] else "redução"
    else:
        tendencia = "estável"

    data_geracao = datetime.now().strftime("%d/%m/%Y às %H:%M")

    # Documento PDF
    doc = SimpleDocTemplate(
        caminho_saida_pdf,
        pagesize=A4,
        topMargin=120,
        bottomMargin=80,
        leftMargin=50,
        rightMargin=50,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Title"],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#0f172a"),
        alignment=1,
        fontName="Helvetica-Bold",
    )
    heading_style = ParagraphStyle(
        "CustomHeading",
        parent=styles["Heading2"],
        fontSize=13,
        leading=17,
        textColor=colors.HexColor("#1e3a8a"),
        spaceBefore=12,
        spaceAfter=6,
        fontName="Helvetica-Bold",
    )
    body_style = ParagraphStyle(
        "CustomBody",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#1e293b"),
        spaceBefore=4,
        spaceAfter=6,
    )

    conteudo: List[object] = []

    # 1. Capa
    conteudo.append(Spacer(1, 100))
    conteudo.append(Paragraph(f"PREFEITURA MUNICIPAL DE {municipio.upper()}", title_style))
    conteudo.append(Spacer(1, 10))
    conteudo.append(
        Paragraph(orgao_emissor, ParagraphStyle("Sub", parent=body_style, alignment=1, fontSize=12))
    )
    conteudo.append(Spacer(1, 30))

    conteudo.append(Paragraph("RELATÓRIO TÉCNICO DE MONITORAMENTO DE QUEIMADAS", heading_style))
    conteudo.append(Spacer(1, 15))
    conteudo.append(Paragraph(f"<b>Unidade Federativa:</b> {estado.title()}", body_style))
    conteudo.append(Paragraph(f"<b>Município em Foco:</b> {municipio.title()}", body_style))
    conteudo.append(Paragraph(f"<b>Data de Emissão:</b> {data_geracao}", body_style))
    conteudo.append(PageBreak())

    # 2. Introdução
    conteudo.append(Paragraph("1. INTRODUÇÃO E CONTEXTUALIZAÇÃO", heading_style))
    conteudo.append(
        Paragraph(
            f"Este documento técnico consolida os dados de monitoramento de focos de calor e queimadas "
            f"para o município de {municipio.title()} ({estado.upper()}), integrando dados satelitais "
            f"fornecidos pelo Instituto Nacional de Pesquisas Espaciais (INPE). O propósito é subsidiar a "
            f"gestão ambiental, a fiscalização preventiva e a elaboração de políticas públicas sustentáveis.",
            body_style,
        )
    )
    conteudo.append(Spacer(1, 15))

    # 3. Resultados Gerais
    conteudo.append(Paragraph("2. DIAGNÓSTICO E RESULTADOS ESTATÍSTICOS", heading_style))
    conteudo.append(
        Paragraph(
            f"No consolidado estadual, o município com maior incidência de focos foi "
            f"<b>{top1['municipio'].title()}</b>, com um total de <b>{int(top1['focos']):,}</b> focos detectados.",
            body_style,
        )
    )
    conteudo.append(
        Paragraph(
            f"O município de <b>{municipio.title()}</b> registrou <b>{focos_mun:,}</b> focos no período analisado, "
            f"ocupando a posição <b>#{pos_municipio}</b> no ranking de focos do estado do {estado.title()}.",
            body_style,
        )
    )
    conteudo.append(
        Paragraph(
            f"A participação relativa de {municipio.title()} equivale a <b>{percentual:.2f}%</b> "
            f"do total de focos observados em todo o território estadual.",
            body_style,
        )
    )
    conteudo.append(Spacer(1, 15))

    # 4. Tendência Temporal
    conteudo.append(Paragraph("3. SÉRIE HISTÓRICA E TENDÊNCIA TEMPORAL", heading_style))
    conteudo.append(
        Paragraph(
            f"A análise da série temporal recente aponta uma tendência de <b>{tendencia}</b> no volume de focos. "
            f"Abaixo estão discriminados os totais anuais computados:",
            body_style,
        )
    )
    for _, row in anual.iterrows():
        conteudo.append(
            Paragraph(
                f"• <b>Ano {int(row['ano'])}:</b> {int(row['focos']):,} focos registrados.",
                body_style,
            )
        )
    conteudo.append(Spacer(1, 15))

    # 4. Análise Territorial em Óbidos (Assentamentos, Quilombolas, UCs e Terras Indígenas)
    conteudo.append(Paragraph("4. ANÁLISE TERRITORIAL EM ÓBIDOS: ASSENTAMENTOS, QUILOMBOLAS, UCs E ÁREAS INDÍGENAS", heading_style))
    conteudo.append(
        Paragraph(
            "Em atendimento às diretrizes de governança socioambiental e ordenamento fundiário, "
            "apresenta-se o diagnóstico espacial estratificado por categorias territoriais de destinação pública, "
            "comunitária e de proteção integral dentro do município de Óbidos.",
            body_style,
        )
    )
    conteudo.append(Spacer(1, 8))

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
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3a8a")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 5),
            ("TOPPADDING", (0, 0), (-1, 0), 5),
            ("ALIGN", (1, 0), (-1, -1), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 1), (-1, -1), 8.5),
            ("BOTTOMPADDING", (0, 1), (-1, -1), 4),
            ("TOPPADDING", (0, 1), (-1, -1), 4),
        ]))
        conteudo.append(Paragraph("<b>Tabela 1 – Distribuição de Queimadas por Categoria Territorial em Óbidos</b>", body_style))
        conteudo.append(Spacer(1, 4))
        conteudo.append(t_cat)
        conteudo.append(Spacer(1, 12))

    # Inclusão de figuras territoriais
    def adicionar_figura(nome_arquivo: str, legenda: str) -> None:
        caminho = os.path.join(diretorio_graficos, nome_arquivo)
        if os.path.exists(caminho):
            conteudo.append(Paragraph(f"<b>{legenda}</b>", body_style))
            conteudo.append(Spacer(1, 4))
            conteudo.append(Image(caminho, width=460, height=230))
            conteudo.append(Spacer(1, 14))
        else:
            logger.debug("Gráfico não encontrado para inclusão no PDF: %s", caminho)

    adicionar_figura("obidos_territorios_barras.png", "Figura 1 – Distribuição de focos por categoria territorial em Óbidos.")
    adicionar_figura("obidos_territorios_pizza.png", "Figura 2 – Proporção relativa de queimadas por categoria fundiária.")
    conteudo.append(PageBreak())

    # 5. Visualizações Gráficas Gerais
    conteudo.append(Paragraph("5. PAINEL DE SÉRIES HISTÓRICAS E SAZONALIDADE", heading_style))
    adicionar_figura(
        f"{municipio.lower()}_evolucao.png",
        "Figura 3 – Evolução temporal geral de focos em Óbidos (2020 a 2026).",
    )
    adicionar_figura(f"{municipio.lower()}_anual.png", "Figura 4 – Distribuição anual comparativa.")
    adicionar_figura(
        f"{municipio.lower()}_heatmap.png", "Figura 5 – Mapa de calor sazonal (Mês × Ano)."
    )

    conteudo.append(PageBreak())

    # Inserir gráficos anuais específicos
    if not anual.empty:
        anos = sorted(anual["ano"].unique())
        for ano in anos:
            conteudo.append(Paragraph(f"Detalhamento do Ano {int(ano)}", heading_style))
            adicionar_figura(
                f"{municipio.lower()}_mensal_{int(ano)}.png", f"Distribuição mensal em {int(ano)}."
            )
            adicionar_figura(f"top10_{int(ano)}.png", f"Top 10 municípios do estado em {int(ano)}.")
            adicionar_figura(
                f"comparacao_{int(ano)}.png", f"Comparação de evolução municipal em {int(ano)}."
            )
            conteudo.append(PageBreak())

    # 6. Conclusões e Recomendações
    conteudo.append(Paragraph("6. CONCLUSÕES E RECOMENDAÇÕES", heading_style))
    conteudo.append(
        Paragraph(
            f"A análise espacial e territorial em {municipio.title()} comprova que a maior pressão "
            f"de queimadas incide sobre áreas de transição e projetos de assentamento, enquanto as Unidades de "
            f"Conservação e Terras Indígenas atuam como barreiras ecológicas vitais. Recomenda-se:",
            body_style,
        )
    )
    conteudo.append(
        Paragraph(
            "a) Fortalecimento de brigadas comunitárias nos Projetos de Assentamento (PAEs) e Territórios Quilombolas;", body_style
        )
    )
    conteudo.append(
        Paragraph(
            "b) Fiscalização integrada permanente nas Unidades de Conservação (FLOTA Trombetas e FLOTA Faro);",
            body_style,
        )
    )
    conteudo.append(
        Paragraph(
            "c) Monitoramento contínuo das bordas de Terras Indígenas (TI Trombetas-Mapuera, TI Zo'é) com alertas automáticos;",
            body_style,
        )
    )
    conteudo.append(
        Paragraph(
            "d) Incentivo ao manejo agroecológico sustentável e assistência técnica aos produtores rurais.",
            body_style,
        )
    )

    # Construir PDF
    doc.build(
        conteudo,
        onFirstPage=lambda c, d: adicionar_fundo_e_paginacao(c, d, logo_path),
        onLaterPages=lambda c, d: adicionar_fundo_e_paginacao(c, d, logo_path),
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
