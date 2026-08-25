"""
Módulo de Tratamento e Padronização de Dados de Queimadas.

Realiza a ingestão de múltiplos arquivos CSV brutos, padronização de
colunas, normalização textual (remoção de acentos e espaços), tratamento
temporal, validação de limites geográficos e geração de subconjuntos tratados.
"""

from __future__ import annotations

import argparse
import glob
import logging
import os
import sys
import unicodedata
from typing import List, Optional, Tuple

import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("queimadas.tratamento")


def normalizar_texto(s: Optional[str]) -> str:
    """Remove acentuação, converte para maiúsculas e remove espaços extras.

    Args:
        s: String ou objeto a ser normalizado.

    Returns:
        String normalizada sem acentos e em caixa alta.
    """
    if pd.isna(s):
        return ""
    s_str = str(s)
    s_norm = unicodedata.normalize("NFKD", s_str)
    s_clean = s_norm.encode("ASCII", "ignore").decode("ASCII")
    return s_clean.upper().strip()


def detectar_coluna_data(df: pd.DataFrame) -> str:
    """Identifica o nome da coluna temporal presente no DataFrame.

    Args:
        df: DataFrame de entrada.

    Returns:
        Nome da coluna identificada.

    Raises:
        ValueError: Se nenhuma coluna de data válida for encontrada.
    """
    colunas_possiveis = ["datahora", "data", "data_pas", "datetime", "timestamp"]
    for col in colunas_possiveis:
        if col in df.columns:
            return col

    logger.error("Colunas presentes: %s", list(df.columns))
    raise ValueError("Nenhuma coluna de data identificada no DataFrame.")


def carregar_arquivos_brutos(padrao_busca: str = "dados/bruto/queimadas_*.csv") -> pd.DataFrame:
    """Carrega e concatena todos os arquivos CSV correspondentes ao padrão de busca.

    Args:
        padrao_busca: Padrão glob para localização dos arquivos brutos.

    Returns:
        DataFrame consolidado com os registros brutos.

    Raises:
        FileNotFoundError: Se nenhum arquivo for encontrado.
    """
    arquivos = sorted(glob.glob(padrao_busca))
    if not arquivos:
        logger.warning("Nenhum arquivo encontrado com o padrão '%s'.", padrao_busca)
        raise FileNotFoundError(f"Nenhum arquivo encontrado em: {padrao_busca}")

    lista_df: List[pd.DataFrame] = []
    for arq in arquivos:
        logger.info("Lendo arquivo bruto: %s", arq)
        try:
            df_temp = pd.read_csv(arq, encoding="utf-8", low_memory=False)
        except (UnicodeDecodeError, Exception):
            df_temp = pd.read_csv(arq, encoding="latin1", low_memory=False)
        lista_df.append(df_temp)

    df_consolidado = pd.concat(lista_df, ignore_index=True)
    logger.info("Total de registros brutos consolidados: %d", len(df_consolidado))
    return df_consolidado


def tratar_dataframe(
    df: pd.DataFrame,
    remover_coordenadas_invalidas: bool = True
) -> pd.DataFrame:
    """Executa o pipeline completo de limpeza e padronização no DataFrame.

    Args:
        df: DataFrame bruto.
        remover_coordenadas_invalidas: Se verdadeiro, valida e filtra limites de latitude e longitude.

    Returns:
        DataFrame limpo, padronizado e com colunas temporais derivadas.
    """
    df_clean = df.copy()
    df_clean.columns = df_clean.columns.str.lower().str.strip()

    # Normalizar nomes de colunas espaciais comuns
    df_clean = df_clean.rename(columns={"lat": "latitude", "lon": "longitude", "long": "longitude"})

    # Tratamento de Data
    col_data = detectar_coluna_data(df_clean)
    df_clean["data"] = pd.to_datetime(df_clean[col_data], errors="coerce")
    df_clean = df_clean.dropna(subset=["data"])

    df_clean["mes"] = df_clean["data"].dt.month
    df_clean["ano"] = df_clean["data"].dt.year

    # Normalização de texto
    if "estado" in df_clean.columns:
        df_clean["estado"] = df_clean["estado"].apply(normalizar_texto)

    if "municipio" in df_clean.columns:
        df_clean["municipio"] = df_clean["municipio"].apply(normalizar_texto)

    if "bioma" in df_clean.columns:
        df_clean["bioma"] = df_clean["bioma"].apply(normalizar_texto)

    # Validação de Coordenadas Geográficas
    if remover_coordenadas_invalidas and "latitude" in df_clean.columns and "longitude" in df_clean.columns:
        df_clean["latitude"] = pd.to_numeric(df_clean["latitude"], errors="coerce")
        df_clean["longitude"] = pd.to_numeric(df_clean["longitude"], errors="coerce")

    # Remover duplicatas exatas
    total_antes = len(df_clean)
    df_clean = df_clean.drop_duplicates()
    duplicatas = total_antes - len(df_clean)
    if duplicatas > 0:
        logger.info("Removidas %d linhas duplicadas.", duplicatas)

    return df_clean


def processar_e_salvar(
    origem_padrao: str = "dados/bruto/queimadas_*.csv",
    destino_dir: str = "dados/tratado",
    estado_foco: str = "PARA",
    municipio_foco: str = "OBIDOS"
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Processa os dados brutos e salva os arquivos tratados para estado e município de foco.

    Args:
        origem_padrao: Padrão de busca dos arquivos brutos.
        destino_dir: Diretório de destino para arquivos tratados.
        estado_foco: Nome normalizado do estado de interesse (ex: 'PARA').
        municipio_foco: Nome normalizado do município de interesse (ex: 'OBIDOS').

    Returns:
        Tupla com (df_completo, df_estado, df_municipio).
    """
    os.makedirs(destino_dir, exist_ok=True)

    df_bruto = carregar_arquivos_brutos(origem_padrao)
    df_tratado = tratar_dataframe(df_bruto)

    # Subconjuntos
    df_estado = (
        df_tratado[df_tratado["estado"].str.contains(estado_foco, na=False)]
        if "estado" in df_tratado.columns else pd.DataFrame()
    )

    df_municipio = (
        df_tratado[df_tratado["municipio"] == municipio_foco]
        if "municipio" in df_tratado.columns else pd.DataFrame()
    )

    # Salvar resultados
    caminho_geral = os.path.join(destino_dir, "queimadas_tratado.csv")
    caminho_estado = os.path.join(destino_dir, f"{estado_foco.lower()}.csv")
    caminho_municipio = os.path.join(destino_dir, f"{municipio_foco.lower()}.csv")

    df_tratado.to_csv(caminho_geral, index=False, encoding="utf-8")
    df_estado.to_csv(caminho_estado, index=False, encoding="utf-8")
    df_municipio.to_csv(caminho_municipio, index=False, encoding="utf-8")

    logger.info("Tratamento concluído com sucesso!")
    logger.info("Total geral: %d | Total %s: %d | Total %s: %d",
                len(df_tratado), estado_foco, len(df_estado), municipio_foco, len(df_municipio))

    return df_tratado, df_estado, df_municipio


def parse_args() -> argparse.Namespace:
    """Configura argumentos de linha de comando."""
    parser = argparse.ArgumentParser(
        description="Tratamento e padronização dos dados brutos de queimadas."
    )
    parser.add_argument(
        "--origem",
        type=str,
        default="dados/bruto/queimadas_*.csv",
        help="Padrão glob para os arquivos de entrada (padrão: dados/bruto/queimadas_*.csv)."
    )
    parser.add_argument(
        "--destino",
        type=str,
        default="dados/tratado",
        help="Diretório de saída para os arquivos tratados (padrão: dados/tratado)."
    )
    parser.add_argument(
        "--estado",
        type=str,
        default="PARA",
        help="Estado de foco para filtragem (padrão: PARA)."
    )
    parser.add_argument(
        "--municipio",
        type=str,
        default="OBIDOS",
        help="Município de foco para filtragem (padrão: OBIDOS)."
    )
    return parser.parse_args()


def main() -> None:
    """Execução principal do script de tratamento."""
    args = parse_args()
    try:
        processar_e_salvar(
            origem_padrao=args.origem,
            destino_dir=args.destino,
            estado_foco=normalizar_texto(args.estado),
            municipio_foco=normalizar_texto(args.municipio)
        )
    except Exception as exc:
        logger.error("Erro durante o tratamento de dados: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
