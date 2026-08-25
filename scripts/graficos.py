"""
Módulo de Geração de Gráficos e Visualizações Estatísticas.

Gera gráficos de barras mensais, séries históricas de evolução,
gráficos de variação percentual, mapas de calor (heatmaps),
rankings municipais e comparativos multi-municipais com alta resolução (DPI).
"""

from __future__ import annotations

import argparse
import logging
import os
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("queimadas.graficos")

# Configurações globais de estilo
plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
plt.rcParams.update({
    "font.sans-serif": ["DejaVu Sans", "Arial", "Helvetica"],
    "axes.edgecolor": "#cbd5e1",
    "axes.linewidth": 0.8,
    "grid.color": "#f1f5f9",
    "grid.linestyle": "--",
})


def salvar_grafico_barra(
    serie: pd.Series,
    titulo: str,
    caminho_saida: str,
    xlabel: str = "Mês",
    ylabel: str = "Quantidade de Focos",
    cor: str = "#2563eb"
) -> None:
    """Gera e salva gráfico de barras com rótulos de valores sobre cada barra.

    Args:
        serie: Série do Pandas contendo os valores indexados.
        titulo: Título do gráfico.
        caminho_saida: Caminho para salvar a imagem PNG.
        xlabel: Rótulo do eixo X.
        ylabel: Rótulo do eixo Y.
        cor: Cor hexadecimal das barras.
    """
    fig, ax = plt.subplots(figsize=(10, 5), dpi=300)
    serie.plot(kind="bar", ax=ax, color=cor, edgecolor="none", width=0.7)

    ax.set_title(titulo, fontsize=14, fontweight="bold", pad=15, color="#0f172a")
    ax.set_xlabel(xlabel, fontsize=11, fontweight="600", labelpad=10, color="#334155")
    ax.set_ylabel(ylabel, fontsize=11, fontweight="600", labelpad=10, color="#334155")
    ax.tick_params(axis="x", rotation=0, labelsize=10)
    ax.tick_params(axis="y", labelsize=10)

    for p in ax.patches:
        altura = p.get_height()
        if altura > 0:
            ax.annotate(
                f"{int(altura):,}".replace(",", "."),
                (p.get_x() + p.get_width() / 2.0, altura),
                ha="center",
                va="bottom",
                fontsize=9,
                fontweight="600",
                color="#1e293b",
                xytext=(0, 3),
                textcoords="offset points"
            )

    plt.tight_layout()
    plt.savefig(caminho_saida, bbox_inches="tight")
    plt.close(fig)


def gerar_graficos_mensais_municipio(
    df_municipio: pd.DataFrame,
    municipio_nome: str,
    diretorio_saida: str
) -> None:
    """Gera gráficos mensais para cada ano disponível no município."""
    if df_municipio.empty:
        return

    anos = sorted(df_municipio["ano"].unique())
    for ano in anos:
        df_ano = df_municipio[df_municipio["ano"] == ano]
        grafico = (
            df_ano.groupby("mes")
            .size()
            .reindex(range(1, 13), fill_value=0)
        )
        meses_labels = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
        grafico.index = meses_labels

        caminho = os.path.join(diretorio_saida, f"{municipio_nome.lower()}_mensal_{ano}.png")
        salvar_grafico_barra(
            grafico,
            f"Focos de Queimadas por Mês – {municipio_nome.title()} ({ano})",
            caminho,
            xlabel="Mês",
            cor="#dc2626"
        )


def gerar_grafico_evolucao_historica(
    df_municipio: pd.DataFrame,
    municipio_nome: str,
    diretorio_saida: str
) -> None:
    """Gera gráfico de linha com evolução contínua ao longo dos anos."""
    if df_municipio.empty:
        return

    serie = (
        df_municipio.groupby(["ano", "mes"])
        .size()
        .reset_index(name="focos")
    )
    serie["data"] = pd.to_datetime(
        serie["ano"].astype(str) + "-" + serie["mes"].astype(str).str.zfill(2) + "-01"
    )
    serie = serie.sort_values("data")

    fig, ax = plt.subplots(figsize=(11, 5), dpi=300)
    ax.plot(
        serie["data"],
        serie["focos"],
        marker="o",
        color="#2563eb",
        linewidth=2.5,
        markersize=6,
        markerfacecolor="#ffffff",
        markeredgewidth=2,
        markeredgecolor="#2563eb"
    )

    ax.set_title(f"Evolução Temporal Geral de Focos – {municipio_nome.title()}", fontsize=14, fontweight="bold", pad=15)
    ax.set_xlabel("Período", fontsize=11, fontweight="600", labelpad=10)
    ax.set_ylabel("Número de Focos", fontsize=11, fontweight="600", labelpad=10)

    plt.tight_layout()
    caminho = os.path.join(diretorio_saida, f"{municipio_nome.lower()}_evolucao.png")
    plt.savefig(caminho, bbox_inches="tight")
    plt.close(fig)


def gerar_graficos_variacao_mensal(
    df_municipio: pd.DataFrame,
    municipio_nome: str,
    diretorio_saida: str
) -> None:
    """Gera gráficos de variação percentual mensal para cada ano."""
    if df_municipio.empty:
        return

    anos = sorted(df_municipio["ano"].unique())
    meses_labels = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]

    for ano in anos:
        df_ano = df_municipio[df_municipio["ano"] == ano]
        serie = (
            df_ano.groupby("mes")
            .size()
            .reindex(range(1, 13), fill_value=0)
        )
        variacao = serie.pct_change() * 100
        variacao = variacao.replace([np.inf, -np.inf], 0).fillna(0)

        fig, ax = plt.subplots(figsize=(10, 5), dpi=300)
        ax.plot(
            range(1, 13),
            variacao.values,
            marker="s",
            color="#7c3aed",
            linewidth=2,
            markersize=6
        )
        ax.axhline(0, color="#94a3b8", linewidth=1.2, linestyle="--")

        ax.set_xticks(range(1, 13))
        ax.set_xticklabels(meses_labels)
        ax.set_title(f"Variação Percentual Mensal (MoM) – {municipio_nome.title()} ({ano})", fontsize=14, fontweight="bold", pad=15)
        ax.set_xlabel("Mês", fontsize=11, fontweight="600")
        ax.set_ylabel("Variação (%)", fontsize=11, fontweight="600")

        plt.tight_layout()
        caminho = os.path.join(diretorio_saida, f"{municipio_nome.lower()}_variacao_{ano}.png")
        plt.savefig(caminho, bbox_inches="tight")
        plt.close(fig)


def gerar_grafico_anual_consolidado(
    df_municipio: pd.DataFrame,
    municipio_nome: str,
    diretorio_saida: str
) -> None:
    """Gera gráfico consolidado anual de focos para o município."""
    if df_municipio.empty:
        return

    anual = df_municipio.groupby("ano").size().sort_index()
    caminho = os.path.join(diretorio_saida, f"{municipio_nome.lower()}_anual.png")
    salvar_grafico_barra(
        anual,
        f"Consolidado Anual de Focos – {municipio_nome.title()}",
        caminho,
        xlabel="Ano",
        cor="#0284c7"
    )


def gerar_heatmap_mensal_anual(
    df_municipio: pd.DataFrame,
    municipio_nome: str,
    diretorio_saida: str
) -> None:
    """Gera mapa de calor relacionando Mês vs Ano para o município."""
    if df_municipio.empty:
        return

    tabela = df_municipio.groupby(["ano", "mes"]).size().unstack(fill_value=0)
    tabela = tabela.reindex(columns=range(1, 13), fill_value=0)
    meses_labels = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
    tabela.columns = meses_labels

    fig, ax = plt.subplots(figsize=(12, 4.5), dpi=300)
    sns.heatmap(
        tabela,
        annot=True,
        fmt="d",
        cmap="YlOrRd",
        cbar_kws={"label": "Quantidade de Focos"},
        linewidths=0.5,
        linecolor="#ffffff",
        ax=ax
    )

    ax.set_title(f"Mapa de Calor de Queimadas (Mês × Ano) – {municipio_nome.title()}", fontsize=14, fontweight="bold", pad=15)
    ax.set_xlabel("Mês", fontsize=11, fontweight="600", labelpad=10)
    ax.set_ylabel("Ano", fontsize=11, fontweight="600", labelpad=10)

    plt.tight_layout()
    caminho = os.path.join(diretorio_saida, f"{municipio_nome.lower()}_heatmap.png")
    plt.savefig(caminho, bbox_inches="tight")
    plt.close(fig)


def gerar_rankings_estaduais(
    df_estado: pd.DataFrame,
    estado_nome: str,
    diretorio_saida: str
) -> None:
    """Gera gráficos de Top 10 municípios do estado para cada ano."""
    if df_estado.empty:
        return

    anos = sorted(df_estado["ano"].unique())
    for ano in anos:
        df_ano = df_estado[df_estado["ano"] == ano]
        ranking = df_ano.groupby("municipio").size().sort_values(ascending=False)
        top10 = ranking.head(10)

        fig, ax = plt.subplots(figsize=(10, 5), dpi=300)
        top10.plot(kind="bar", ax=ax, color="#ea580c", edgecolor="none", width=0.7)

        ax.set_title(f"Top 10 Municípios com Mais Focos – {estado_nome.title()} ({ano})", fontsize=14, fontweight="bold", pad=15)
        ax.set_xlabel("Município", fontsize=11, fontweight="600", labelpad=10)
        ax.set_ylabel("Quantidade de Focos", fontsize=11, fontweight="600", labelpad=10)
        ax.tick_params(axis="x", rotation=35, labelsize=9)

        for p in ax.patches:
            altura = p.get_height()
            if altura > 0:
                ax.annotate(
                    f"{int(altura):,}".replace(",", "."),
                    (p.get_x() + p.get_width() / 2.0, altura),
                    ha="center",
                    va="bottom",
                    fontsize=8.5,
                    fontweight="600",
                    xytext=(0, 2),
                    textcoords="offset points"
                )

        plt.tight_layout()
        caminho = os.path.join(diretorio_saida, f"top10_{ano}.png")
        plt.savefig(caminho, bbox_inches="tight")
        plt.close(fig)


def gerar_comparativo_municipios(
    df_estado: pd.DataFrame,
    municipio_alvo: str,
    diretorio_saida: str
) -> None:
    """Gera gráfico comparativo entre os top 5 municípios e o município de foco."""
    if df_estado.empty:
        return

    ranking_geral = df_estado.groupby("municipio").size().sort_values(ascending=False)
    top_municipios = ranking_geral.head(5).index.tolist()

    if municipio_alvo.upper() not in top_municipios:
        top_municipios.append(municipio_alvo.upper())

    anos_disponiveis = sorted(df_estado["ano"].unique())
    meses_labels = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
    paleta = sns.color_palette("tab10", len(top_municipios))

    for ano in anos_disponiveis:
        df_ano = df_estado[df_estado["ano"] == ano]
        fig, ax = plt.subplots(figsize=(11, 5.5), dpi=300)

        for idx, municipio in enumerate(top_municipios):
            df_mun = df_ano[df_ano["municipio"] == municipio]
            serie = df_mun.groupby("mes").size().reindex(range(1, 13), fill_value=0)

            is_target = (municipio == municipio_alvo.upper())
            ax.plot(
                range(1, 13),
                serie.values,
                marker="o" if is_target else "s",
                linewidth=3 if is_target else 1.8,
                label=f"{municipio.title()}{' ★' if is_target else ''}",
                color=paleta[idx]
            )

        ax.set_xticks(range(1, 13))
        ax.set_xticklabels(meses_labels)
        ax.set_title(f"Evolução Mensal Comparativa entre Municípios – {ano}", fontsize=14, fontweight="bold", pad=15)
        ax.set_xlabel("Mês", fontsize=11, fontweight="600")
        ax.set_ylabel("Número de Focos", fontsize=11, fontweight="600")
        ax.legend(title="Município", frameon=True)

        plt.tight_layout()
        caminho = os.path.join(diretorio_saida, f"comparacao_{ano}.png")
        plt.savefig(caminho, bbox_inches="tight")
        plt.close(fig)


def gerar_todos_graficos(
    caminho_csv: str = "dados/tratado/queimadas_tratado.csv",
    diretorio_saida: str = "outputs/graficos",
    estado: str = "PARA",
    municipio: str = "OBIDOS"
) -> None:
    """Orquestra a geração de todo o catálogo de gráficos técnicos."""
    os.makedirs(diretorio_saida, exist_ok=True)

    if not os.path.exists(caminho_csv):
        raise FileNotFoundError(f"Arquivo CSV não encontrado em: {caminho_csv}")

    df = pd.read_csv(caminho_csv)
    df["data"] = pd.to_datetime(df["data"], errors="coerce")
    df = df.dropna(subset=["data"])
    df["mes"] = df["data"].dt.month
    df["ano"] = df["data"].dt.year
    df["estado"] = df["estado"].astype(str).str.upper().str.strip()
    df["municipio"] = df["municipio"].astype(str).str.upper().str.strip()

    df_estado = df[df["estado"].str.contains(estado.upper(), na=False)]
    df_municipio = df[df["municipio"] == municipio.upper()]

    logger.info("Gerando gráficos para %s (%s)...", municipio, estado)
    gerar_graficos_mensais_municipio(df_municipio, municipio, diretorio_saida)
    gerar_grafico_evolucao_historica(df_municipio, municipio, diretorio_saida)
    gerar_graficos_variacao_mensal(df_municipio, municipio, diretorio_saida)
    gerar_grafico_anual_consolidado(df_municipio, municipio, diretorio_saida)
    gerar_heatmap_mensal_anual(df_municipio, municipio, diretorio_saida)
    gerar_rankings_estaduais(df_estado, estado, diretorio_saida)
    gerar_comparativo_municipios(df_estado, municipio, diretorio_saida)

    logger.info("Todos os gráficos foram gerados e salvos com sucesso em: %s", diretorio_saida)


def parse_args() -> argparse.Namespace:
    """Configura argumentos de linha de comando."""
    parser = argparse.ArgumentParser(description="Gera visualizações gráficas para análise de queimadas.")
    parser.add_argument(
        "--dados",
        type=str,
        default="dados/tratado/queimadas_tratado.csv",
        help="Caminho do arquivo tratado CSV."
    )
    parser.add_argument(
        "--saida",
        type=str,
        default="outputs/graficos",
        help="Diretório de saída para as imagens PNG geradas."
    )
    parser.add_argument(
        "--estado",
        type=str,
        default="PARA",
        help="Estado alvo."
    )
    parser.add_argument(
        "--municipio",
        type=str,
        default="OBIDOS",
        help="Município alvo."
    )
    return parser.parse_args()


def main() -> None:
    """Ponto de entrada do script."""
    args = parse_args()
    try:
        gerar_todos_graficos(
            caminho_csv=args.dados,
            diretorio_saida=args.saida,
            estado=args.estado,
            municipio=args.municipio
        )
    except Exception as exc:
        logger.error("Erro na geração de gráficos: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
