"""
Testes unitários para o módulo de análise (scripts/analise.py).
"""

import pandas as pd

from scripts.analise import (
    calcular_ranking_municipios,
    calcular_series_temporais,
    identificar_eventos_extremos,
)


def test_calcular_ranking_municipios(dados_tratados_exemplo):
    ranking = calcular_ranking_municipios(dados_tratados_exemplo)

    assert not ranking.empty
    assert "municipio" in ranking.columns
    assert "focos" in ranking.columns

    # OBIDOS tem 7 registros no dataset de teste
    primeiro = ranking.iloc[0]
    assert primeiro["municipio"] == "OBIDOS"
    assert primeiro["focos"] == 7


def test_calcular_series_temporais(dados_tratados_exemplo):
    serie_mensal, serie_anual = calcular_series_temporais(dados_tratados_exemplo)

    assert not serie_mensal.empty
    assert "variacao_%" in serie_mensal.columns
    assert set(serie_anual["ano"].unique()) == {2023, 2024}

    total_focos = serie_anual["focos"].sum()
    assert total_focos == len(dados_tratados_exemplo)


def test_identificar_eventos_extremos():
    serie = pd.DataFrame({
        "ano": [2024, 2024, 2024, 2024],
        "mes": [1, 2, 3, 4],
        "focos": [10, 20, 10, 50],
        "variacao_%": [0.0, 100.0, -50.0, 400.0]
    })
    aumento, queda = identificar_eventos_extremos(serie, limiar_percentual=30.0)

    assert len(aumento) == 2  # meses 2 e 4
    assert len(queda) == 1   # mês 3
