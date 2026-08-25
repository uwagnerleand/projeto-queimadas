"""
Testes unitários para o módulo de coleta (scripts/coleta.py).
"""

import pandas as pd
import pytest

from scripts.coleta import detectar_coluna_data, normalizar_json


def test_detectar_coluna_data_sucesso():
    df1 = pd.DataFrame({"datahora": ["2024-01-01"], "focos": [10]})
    assert detectar_coluna_data(df1) == "datahora"

    df2 = pd.DataFrame({"data": ["2024-01-01"], "focos": [10]})
    assert detectar_coluna_data(df2) == "data"

    df3 = pd.DataFrame({"data_pas": ["2024-01-01"], "focos": [10]})
    assert detectar_coluna_data(df3) == "data_pas"


def test_detectar_coluna_data_invalida():
    df = pd.DataFrame({"coluna_a": [1, 2], "coluna_b": [3, 4]})
    with pytest.raises(ValueError, match="Nenhuma coluna de data válida"):
        detectar_coluna_data(df)


def test_normalizar_json_lista():
    data = [
        {"id": 1, "municipio": "OBIDOS", "focos": 50},
        {"id": 2, "municipio": "SANTAREM", "focos": 120},
    ]
    df = normalizar_json(data)
    assert len(df) == 2
    assert "municipio" in df.columns
    assert df.loc[0, "municipio"] == "OBIDOS"


def test_normalizar_json_dicionario_com_data():
    data = {
        "data": [
            {"id": 1, "estado": "PARA"},
            {"id": 2, "estado": "AMAZONAS"},
        ]
    }
    df = normalizar_json(data)
    assert len(df) == 2
    assert "estado" in df.columns


def test_normalizar_json_invalido():
    with pytest.raises(ValueError, match="Formato JSON inesperado"):
        normalizar_json("string_invalida")
