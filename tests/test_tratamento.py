"""
Testes unitários para o módulo de tratamento (scripts/tratamento.py).
"""

import pandas as pd

from scripts.tratamento import normalizar_texto, tratar_dataframe


def test_normalizar_texto():
    assert normalizar_texto("Pará") == "PARA"
    assert normalizar_texto("  Óbidos  ") == "OBIDOS"
    assert normalizar_texto("São Félix do Xingu") == "SAO FELIX DO XINGU"
    assert normalizar_texto("Santarém") == "SANTAREM"
    assert normalizar_texto(None) == ""


def test_tratar_dataframe_limpeza_e_colunas(dados_brutos_exemplo):
    df_resultado = tratar_dataframe(dados_brutos_exemplo)

    # Verifica colunas derivadas
    assert "data" in df_resultado.columns
    assert "ano" in df_resultado.columns
    assert "mes" in df_resultado.columns
    assert "latitude" in df_resultado.columns
    assert "longitude" in df_resultado.columns

    # Verifica remoção de duplicatas (dados_brutos_exemplo tinha 6 linhas, 1 duplicada)
    assert len(df_resultado) == 5

    # Verifica normalização de texto
    assert all(df_resultado["estado"] == "PARA")
    assert "OBIDOS" in df_resultado["municipio"].values
    assert "SANTAREM" in df_resultado["municipio"].values


def test_tratar_dataframe_datas_validas(dados_brutos_exemplo):
    df_resultado = tratar_dataframe(dados_brutos_exemplo)
    assert pd.api.types.is_datetime64_any_dtype(df_resultado["data"])
    assert df_resultado["ano"].nunique() == 1
    assert df_resultado["ano"].iloc[0] == 2024
