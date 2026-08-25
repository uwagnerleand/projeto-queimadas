"""
Configurações e fixtures para a suíte de testes do Projeto Queimadas.
"""

import pandas as pd
import pytest


@pytest.fixture
def dados_brutos_exemplo() -> pd.DataFrame:
    """Retorna um DataFrame simulando a estrutura bruta recebida do INPE."""
    return pd.DataFrame(
        {
            "datahora": [
                "2024/08/15 14:30:00",
                "2024/08/15 15:45:00",
                "2024/09/10 18:20:00",
                "2024/09/11 12:10:00",
                "2024/10/05 08:00:00",
                "2024/10/05 08:00:00",  # duplicata intencional
            ],
            "lat": [-1.908, -1.912, -2.105, -3.200, -1.905, -1.905],
            "lon": [-55.518, -55.520, -54.980, -52.100, -55.510, -55.510],
            "estado": ["Pará", "PARÁ", "Pará", "Pará", "Pará", "Pará"],
            "municipio": ["Óbidos", "ÓBIDOS", "Santarém", "Altamira", "Óbidos", "Óbidos"],
            "bioma": ["Amazônia", "Amazônia", "Amazônia", "Amazônia", "Amazônia", "Amazônia"],
            "satelite": ["AQUA_M-T", "AQUA_M-T", "TERRA_M-T", "NOAA-20", "AQUA_M-T", "AQUA_M-T"],
        }
    )


@pytest.fixture
def dados_tratados_exemplo() -> pd.DataFrame:
    """Retorna um DataFrame já tratado e padronizado para testes analíticos."""
    return pd.DataFrame(
        {
            "data": pd.to_datetime(
                [
                    "2023-08-01",
                    "2023-08-15",
                    "2023-09-01",
                    "2023-09-20",
                    "2024-08-05",
                    "2024-08-20",
                    "2024-09-10",
                    "2024-09-25",
                    "2024-10-01",
                    "2024-10-15",
                ]
            ),
            "ano": [2023, 2023, 2023, 2023, 2024, 2024, 2024, 2024, 2024, 2024],
            "mes": [8, 8, 9, 9, 8, 8, 9, 9, 10, 10],
            "estado": ["PARA"] * 10,
            "municipio": [
                "OBIDOS",
                "OBIDOS",
                "OBIDOS",
                "SANTAREM",
                "OBIDOS",
                "ALTAMIRA",
                "OBIDOS",
                "OBIDOS",
                "SANTAREM",
                "OBIDOS",
            ],
            "latitude": [
                -1.908,
                -1.910,
                -1.912,
                -2.443,
                -1.905,
                -3.203,
                -1.907,
                -1.909,
                -2.440,
                -1.915,
            ],
            "longitude": [
                -55.518,
                -55.520,
                -55.522,
                -54.708,
                -55.510,
                -52.206,
                -55.512,
                -55.515,
                -54.710,
                -55.518,
            ],
        }
    )
