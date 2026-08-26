"""
Módulo de Coleta de Dados de Queimadas.

Responsável por obter dados brutos de focos de queimadas a partir do
servidor público do INPE (formato ZIP/CSV) ou de endpoints de APIs JSON.
"""

from __future__ import annotations

import argparse
import io
import logging
import os
import sys
import zipfile
from typing import Any, Dict, List, Optional, Union

import pandas as pd
import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("queimadas.coleta")


def detectar_coluna_data(df: pd.DataFrame) -> str:
    """Detecta automaticamente o nome da coluna temporal presente no DataFrame.

    Args:
        df: DataFrame contendo os dados brutos.

    Returns:
        Nome da coluna identificada ('datahora', 'data', ou 'data_pas').

    Raises:
        ValueError: Se nenhuma coluna de data reconhecida for encontrada.
    """
    colunas_possiveis = ["datahora", "data", "data_pas", "datetime", "timestamp"]
    for col in colunas_possiveis:
        if col in df.columns:
            return col

    logger.error("Colunas disponíveis no DataFrame: %s", list(df.columns))
    raise ValueError("Nenhuma coluna de data válida encontrada no conjunto de dados.")


def normalizar_json(data: Union[List[Any], Dict[str, Any]]) -> pd.DataFrame:
    """Converte estruturas JSON (listas ou dicionários aninhados) em um DataFrame normalizado.

    Args:
        data: Dados brutos retornados por uma API JSON.

    Returns:
        DataFrame estruturado e tabulado.

    Raises:
        ValueError: Se a estrutura do JSON não puder ser convertida.
    """
    if isinstance(data, list):
        return pd.json_normalize(data)

    if isinstance(data, dict):
        if "data" in data and isinstance(data["data"], list):
            return pd.json_normalize(data["data"])

        if len(data) == 1:
            item = next(iter(data.values()))
            if isinstance(item, list):
                return pd.json_normalize(item)

        return pd.json_normalize(data)

    raise ValueError("Formato JSON inesperado. Esperava-se uma lista ou dicionário estruturado.")


def carregar_dados_api_json(url: str, timeout: int = 30) -> pd.DataFrame:
    """Realiza requisição HTTP a uma API e converte os dados JSON em DataFrame.

    Args:
        url: URL do endpoint REST/JSON.
        timeout: Tempo limite da requisição em segundos.

    Returns:
        DataFrame preenchido com os dados obtidos.
    """
    logger.info("Baixando dados da API: %s", url)
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ProjetoQueimadas/1.0"}
    response = requests.get(url, headers=headers, timeout=timeout)
    response.raise_for_status()

    data = response.json()
    df = normalizar_json(data)
    logger.info("Dados carregados com sucesso: %d registros obtidos.", len(df))
    return df


def carregar_dados_ano_corrente_2026(timeout: int = 60) -> pd.DataFrame:
    """Baixa e consolida os dados mensais do ano de 2026 até agosto de 2026.

    Returns:
        DataFrame com todos os focos registrados em 2026.
    """
    logger.info("Iniciando download dos dados mensais de 2026 (Janeiro a Agosto de 2026)...")
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ProjetoQueimadas/1.0"}
    dfs_meses: List[pd.DataFrame] = []

    for mes in range(1, 9):
        mes_str = f"2026{mes:02d}"
        url = f"https://dataserver-coids.inpe.br/queimadas/queimadas/focos/csv/mensal/Brasil/focos_mensal_br_{mes_str}.csv"
        try:
            r = requests.get(url, headers=headers, timeout=timeout)
            if r.status_code == 200:
                df_m = pd.read_csv(io.BytesIO(r.content), low_memory=False)
                logger.info("  Mês %s carregado: %d registros.", mes_str, len(df_m))
                dfs_meses.append(df_m)
        except Exception as err:
            logger.warning("Falha ao baixar mês %s: %s", mes_str, err)

    if not dfs_meses:
        raise FileNotFoundError("Não foi possível obter os dados de 2026 do INPE.")

    df_2026 = pd.concat(dfs_meses, ignore_index=True)
    df_2026.columns = df_2026.columns.str.lower().str.strip()

    if "estado" in df_2026.columns:
        df_2026["estado"] = df_2026["estado"].astype(str).str.upper().str.strip()
    if "municipio" in df_2026.columns:
        df_2026["municipio"] = df_2026["municipio"].astype(str).str.upper().str.strip()

    col_data = detectar_coluna_data(df_2026)
    df_2026["data"] = pd.to_datetime(df_2026[col_data], errors="coerce")
    df_2026 = df_2026.dropna(subset=["data"])
    df_2026["mes"] = df_2026["data"].dt.month
    df_2026["ano"] = df_2026["data"].dt.year

    logger.info("Download de 2026 concluído com sucesso: %d registros.", len(df_2026))
    return df_2026


def carregar_dados_anual_zip(ano: Union[int, str], timeout: int = 60) -> pd.DataFrame:
    """Baixa o arquivo compactado anual do satélite de referência do INPE e retorna um DataFrame.

    Args:
        ano: Ano dos dados desejados (ex: 2026, 2025, 2024, 2023, 2022).
        timeout: Tempo limite da requisição em segundos.

    Returns:
        DataFrame contendo os registros de queimadas processados para o ano.
    """
    ano_int = int(str(ano).strip())
    if ano_int == 2026:
        return carregar_dados_ano_corrente_2026(timeout=timeout)

    ano_str = str(ano_int)
    url = (
        f"https://dataserver-coids.inpe.br/queimadas/queimadas/focos/csv/anual/Brasil_sat_ref/"
        f"focos_br_ref_{ano_str}.zip"
    )

    logger.info("Iniciando download dos dados do INPE para o ano %s...", ano_str)
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ProjetoQueimadas/1.0"}

    response = requests.get(url, headers=headers, timeout=timeout)
    response.raise_for_status()

    with zipfile.ZipFile(io.BytesIO(response.content)) as zip_file:
        arquivos = zip_file.namelist()
        logger.info("Arquivos encontrados no pacote ZIP: %s", arquivos)

        csv_candidatos = [f for f in arquivos if f.lower().endswith(".csv")]
        if not csv_candidatos:
            raise FileNotFoundError(
                f"Nenhum arquivo CSV encontrado dentro do ZIP para o ano {ano_str}."
            )

        nome_csv = csv_candidatos[0]
        logger.info("Extraindo e processando arquivo: %s", nome_csv)

        try:
            with zip_file.open(nome_csv) as f:
                df = pd.read_csv(f, low_memory=False)
        except UnicodeDecodeError:
            with zip_file.open(nome_csv) as f:
                df = pd.read_csv(f, encoding="latin1", low_memory=False)

    df.columns = df.columns.str.lower().str.strip()

    if "estado" in df.columns:
        df["estado"] = df["estado"].astype(str).str.upper().str.strip()

    if "municipio" in df.columns:
        df["municipio"] = df["municipio"].astype(str).str.upper().str.strip()

    col_data = detectar_coluna_data(df)
    df["data"] = pd.to_datetime(df[col_data], errors="coerce")
    df = df.dropna(subset=["data"])

    df["mes"] = df["data"].dt.month
    df["ano"] = df["data"].dt.year

    logger.info("Download concluído com sucesso para %s. Registros válidos: %d", ano_str, len(df))
    return df


def salvar_dataframe(
    df: pd.DataFrame, nome_arquivo: str, diretorio_destino: Optional[str] = None
) -> str:
    """Salva o DataFrame em formato CSV no diretório especificado.

    Args:
        df: DataFrame a ser salvo.
        nome_arquivo: Nome do arquivo (com ou sem extensão .csv).
        diretorio_destino: Caminho da pasta de destino (padrão: dados/bruto).

    Returns:
        Caminho absoluto do arquivo salvo.
    """
    if diretorio_destino is None:
        raiz = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        pasta = os.path.join(raiz, "dados", "bruto")
    else:
        pasta = diretorio_destino

    os.makedirs(pasta, exist_ok=True)

    if not nome_arquivo.endswith(".csv"):
        nome_arquivo = f"{nome_arquivo}.csv"

    caminho = os.path.join(pasta, nome_arquivo)
    df.to_csv(caminho, index=False, encoding="utf-8")
    logger.info("Arquivo salvo com sucesso em: %s", caminho)
    return caminho


def parse_args() -> argparse.Namespace:
    """Configura e processa os argumentos de linha de comando."""
    parser = argparse.ArgumentParser(
        description="Coleta dados de focos de queimadas do INPE ou APIs externas."
    )
    parser.add_argument(
        "--fonte",
        choices=["inpe", "ibge"],
        default=None,
        help="Fonte dos dados: 'inpe' para servidor do INPE ou 'ibge' para API JSON.",
    )
    parser.add_argument(
        "--ano", type=str, default=None, help="Ano de referência para download do INPE (ex: 2024)."
    )
    parser.add_argument(
        "--url", type=str, default=None, help="URL da API JSON (quando --fonte for ibge)."
    )
    parser.add_argument(
        "--saida", type=str, default=None, help="Nome personalizado para o arquivo de saída."
    )
    return parser.parse_args()


def main() -> None:
    """Ponto de entrada principal para execução via CLI ou interativa."""
    args = parse_args()

    fonte = args.fonte
    if fonte is None:
        if not sys.stdin.isatty():
            fonte = "inpe"
            ano = args.ano or "2024"
        else:
            fonte = (
                input("Escolha a fonte de dados [inpe/ibge] (padrão: inpe): ").strip().lower()
                or "inpe"
            )

    if fonte == "ibge":
        url = args.url
        if not url:
            url = input("Digite a URL da API IBGE ou JSON: ").strip()
        if not url:
            logger.error("A URL não pode estar vazia.")
            sys.exit(1)
        df = carregar_dados_api_json(url)
        nome_arquivo = args.saida or "queimadas_ibge"
    elif fonte == "inpe":
        ano = args.ano
        if not ano:
            ano = input("Digite o ano desejado (ex: 2024): ").strip() or "2024"
        if not str(ano).isdigit():
            logger.error("Ano inválido: '%s'. Digite apenas dígitos.", ano)
            sys.exit(1)
        df = carregar_dados_anual_zip(ano)
        nome_arquivo = args.saida or f"queimadas_{ano}"
    else:
        logger.error("Fonte inválida: '%s'. Escolha 'inpe' ou 'ibge'.", fonte)
        sys.exit(1)

    salvar_dataframe(df, nome_arquivo)


if __name__ == "__main__":
    main()
