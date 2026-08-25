"""
Módulo de Análise Estatística e Métricas de Queimadas.

Calcula rankings municipais, representatividade percentual,
séries temporais mensais e anuais, variações percentuais (MoM/YoY)
e detecção de anomalias/eventos extremos de focos de calor.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from typing import Dict, Optional, Tuple

import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("queimadas.analise")


def carregar_dados_tratados(caminho_csv: str = "dados/tratado/queimadas_tratado.csv") -> pd.DataFrame:
    """Carrega o arquivo CSV tratado e valida os tipos temporais.

    Args:
        caminho_csv: Caminho para o arquivo CSV tratado.

    Returns:
        DataFrame com colunas formatadas e datas válidas.
    """
    if not os.path.exists(caminho_csv):
        logger.error("Arquivo tratado não encontrado: %s", caminho_csv)
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho_csv}")

    df = pd.read_csv(caminho_csv)
    df["data"] = pd.to_datetime(df["data"], errors="coerce")
    df = df.dropna(subset=["data"])

    df["mes"] = df["data"].dt.month
    df["ano"] = df["data"].dt.year

    if "estado" in df.columns:
        df["estado"] = df["estado"].astype(str).str.upper().str.strip()
    if "municipio" in df.columns:
        df["municipio"] = df["municipio"].astype(str).str.upper().str.strip()

    logger.info("Dados carregados com sucesso de %s: %d registros.", caminho_csv, len(df))
    return df


def calcular_ranking_municipios(df_estado: pd.DataFrame) -> pd.DataFrame:
    """Gera ranking consolidado dos municípios por número total de focos de calor.

    Args:
        df_estado: DataFrame filtrado para um determinado estado.

    Returns:
        DataFrame ordenado com as colunas ['municipio', 'focos'].
    """
    if df_estado.empty or "municipio" not in df_estado.columns:
        return pd.DataFrame(columns=["municipio", "focos"])

    ranking = (
        df_estado.groupby("municipio")
        .size()
        .sort_values(ascending=False)
        .reset_index(name="focos")
    )
    return ranking


def calcular_series_temporais(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Calcula séries temporais agregadas por (ano, mês) e por ano.

    Args:
        df: DataFrame contendo as colunas 'ano' e 'mes'.

    Returns:
        Tupla contendo (serie_mensal, serie_anual).
    """
    if df.empty:
        return pd.DataFrame(columns=["ano", "mes", "focos", "variacao_%"]), pd.DataFrame(columns=["ano", "focos"])

    serie_mensal = (
        df.groupby(["ano", "mes"])
        .size()
        .reset_index(name="focos")
        .sort_values(["ano", "mes"])
    )
    serie_mensal["variacao_%"] = serie_mensal["focos"].pct_change() * 100

    serie_anual = (
        df.groupby("ano")
        .size()
        .reset_index(name="focos")
        .sort_values("ano")
    )
    return serie_mensal, serie_anual


def identificar_eventos_extremos(
    serie_mensal: pd.DataFrame,
    limiar_percentual: float = 30.0
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Identifica períodos com surtos (aumentos bruscos) ou reduções expressivas de focos.

    Args:
        serie_mensal: DataFrame com as colunas 'focos' e 'variacao_%'.
        limiar_percentual: Limite percentual para classificar evento extremo.

    Returns:
        Tupla com (eventos_aumento, eventos_queda).
    """
    if serie_mensal.empty or "variacao_%" not in serie_mensal.columns:
        empty = pd.DataFrame(columns=["ano", "mes", "focos", "variacao_%"])
        return empty, empty

    aumento = serie_mensal[serie_mensal["variacao_%"] > limiar_percentual].copy()
    queda = serie_mensal[serie_mensal["variacao_%"] < -limiar_percentual].copy()
    return aumento, queda


def executar_analise(
    caminho_entrada: str = "dados/tratado/queimadas_tratado.csv",
    diretorio_saida: str = "outputs/analise",
    estado_alvo: str = "PARA",
    municipio_alvo: str = "OBIDOS"
) -> Dict[str, pd.DataFrame]:
    """Executa a análise estatística completa e exporta relatórios tabulares.

    Args:
        caminho_entrada: Caminho do arquivo tratado.
        diretorio_saida: Diretório para armazenamento dos CSVs de saída.
        estado_alvo: Estado selecionado para análise comparativa.
        municipio_alvo: Município selecionado para análise em profundidade.

    Returns:
        Dicionário contendo os DataFrames resultantes.
    """
    os.makedirs(diretorio_saida, exist_ok=True)
    df = carregar_dados_tratados(caminho_entrada)

    # Filtragem
    df_estado = (
        df[df["estado"].str.contains(estado_alvo, na=False)]
        if "estado" in df.columns else pd.DataFrame()
    )
    df_municipio = (
        df[df["municipio"] == municipio_alvo]
        if "municipio" in df.columns else pd.DataFrame()
    )

    # Rankings
    ranking = calcular_ranking_municipios(df_estado)
    top10 = ranking.head(10)

    # Posição e representatividade
    total_estado = len(df_estado)
    total_municipio = len(df_municipio)
    percentual = (total_municipio / total_estado * 100) if total_estado > 0 else 0.0

    posicao_municipio: Optional[int] = None
    if not ranking.empty and municipio_alvo in ranking["municipio"].values:
        idx = ranking[ranking["municipio"] == municipio_alvo].index
        posicao_municipio = int(idx[0]) + 1

    logger.info("=== Resultados da Análise ===")
    logger.info("Top 10 Municípios no estado %s:", estado_alvo)
    for _, row in top10.iterrows():
        logger.info("  - %s: %d focos", row["municipio"], row["focos"])

    if posicao_municipio is not None:
        logger.info("Posição de %s no ranking: #%d (%d focos)", municipio_alvo, posicao_municipio, total_municipio)
    logger.info("Representatividade de %s: %.2f%% do total do estado", municipio_alvo, percentual)

    # Séries Temporais
    serie_estado, anual_estado = calcular_series_temporais(df_estado)
    serie_municipio, anual_municipio = calcular_series_temporais(df_municipio)

    # Eventos Extremos
    aumento_estado, queda_estado = identificar_eventos_extremos(serie_estado)
    aumento_mun, queda_mun = identificar_eventos_extremos(serie_municipio)

    # Exportação dos arquivos de análise
    resultados = {
        "ranking_municipios": ranking,
        "top10_municipios": top10,
        "serie_para": serie_estado,
        "serie_obidos": serie_municipio,
        "anual_para": anual_estado,
        "anual_obidos": anual_municipio,
        "aumento_para": aumento_estado,
        "queda_para": queda_estado,
        "aumento_obidos": aumento_mun,
        "queda_obidos": queda_mun,
    }

    for nome, dframe in resultados.items():
        caminho = os.path.join(diretorio_saida, f"{nome}.csv")
        dframe.to_csv(caminho, index=False, encoding="utf-8")

    logger.info("Análise concluída com sucesso. Arquivos salvos em: %s", diretorio_saida)
    return resultados


def parse_args() -> argparse.Namespace:
    """Configura argumentos de linha de comando."""
    parser = argparse.ArgumentParser(description="Executa análise estatística dos dados de queimadas.")
    parser.add_argument(
        "--entrada",
        type=str,
        default="dados/tratado/queimadas_tratado.csv",
        help="Caminho do arquivo CSV tratado de entrada."
    )
    parser.add_argument(
        "--saida-dir",
        type=str,
        default="outputs/analise",
        help="Diretório de saída para os relatórios estatísticos."
    )
    parser.add_argument(
        "--estado",
        type=str,
        default="PARA",
        help="Estado alvo da análise."
    )
    parser.add_argument(
        "--municipio",
        type=str,
        default="OBIDOS",
        help="Município alvo da análise."
    )
    return parser.parse_args()


def main() -> None:
    """Ponto de entrada do script."""
    args = parse_args()
    try:
        executar_analise(
            caminho_entrada=args.entrada,
            diretorio_saida=args.saida_dir,
            estado_alvo=args.estado.upper().strip(),
            municipio_alvo=args.municipio.upper().strip()
        )
    except Exception as exc:
        logger.error("Falha ao executar análise estatística: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
