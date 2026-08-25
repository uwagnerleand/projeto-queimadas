"""
Testes de integração para o pipeline de dados (scripts/pipeline.py).
"""

from unittest.mock import patch

from scripts.pipeline import executar_pipeline, parse_args


def test_parse_args():
    with patch(
        "sys.argv",
        ["run_pipeline.py", "--pular-coleta", "--estado", "AMAZONAS", "--municipio", "MANAUS"],
    ):
        args = parse_args()
        assert args.pular_coleta is True
        assert args.estado == "AMAZONAS"
        assert args.municipio == "MANAUS"


def test_executar_pipeline_mock():
    with (
        patch("scripts.pipeline.processar_e_salvar"),
        patch("scripts.pipeline.executar_analise") as mock_analise,
        patch("scripts.pipeline.gerar_todos_graficos") as mock_graficos,
        patch("scripts.pipeline.gerar_relatorio_pdf") as mock_relatorio,
    ):
        sucesso = executar_pipeline(pular_coleta=True, estado="PARA", municipio="OBIDOS")
        assert sucesso is True
        assert mock_analise.called
        assert mock_graficos.called
        assert mock_relatorio.called
