"""
Orquestrador do Pipeline de Dados - Projeto Queimadas.

Executa de ponta a ponta o ciclo de dados:
1. Coleta (Download INPE ou API)
2. Tratamento e Padronização
3. Análise Estatística e Métricas
4. Geração de Gráficos em Alta Resolução
5. Compilação do Relatório Técnico Oficial em PDF
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
import time
from typing import List, Optional

from scripts.analise import executar_analise
from scripts.coleta import carregar_dados_anual_zip, salvar_dataframe
from scripts.graficos import gerar_todos_graficos
from scripts.relatorio import gerar_relatorio_pdf
from scripts.tratamento import processar_e_salvar

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("queimadas.pipeline")


def executar_pipeline(
    anos: Optional[List[int]] = None,
    pular_coleta: bool = False,
    estado: str = "PARA",
    municipio: str = "OBIDOS",
    dados_brutos_dir: str = "dados/bruto",
    dados_tratados_dir: str = "dados/tratado",
    outputs_dir: str = "outputs",
) -> bool:
    """Executa todas as etapas do pipeline de dados de forma sequencial e controlada.

    Args:
        anos: Lista de anos para baixar caso a coleta seja executada.
        pular_coleta: Se True, pula a etapa de download e usa os dados locais existentes.
        estado: Estado para análises específicas.
        municipio: Município para análises em profundidade.
        dados_brutos_dir: Diretório para armazenamento dos dados brutos.
        dados_tratados_dir: Diretório dos dados tratados.
        outputs_dir: Diretório raiz para relatórios e gráficos.

    Returns:
        True se todas as etapas foram concluídas com sucesso.
    """
    inicio = time.time()
    logger.info("=========================================================")
    logger.info("🚀 INICIANDO PIPELINE DE DADOS - PROJETO QUEIMADAS")
    logger.info("📍 Estado Alvo: %s | Município Alvo: %s", estado, municipio)
    logger.info("=========================================================")

    if anos is None:
        anos = [2020, 2021, 2022, 2024]

    # 1. Coleta
    if not pular_coleta:
        logger.info("\n--- [ETAPA 1/5] Coleta de Dados do INPE ---")
        os.makedirs(dados_brutos_dir, exist_ok=True)
        for ano in anos:
            try:
                logger.info("📥 Coletando dados para o ano %d...", ano)
                df_ano = carregar_dados_anual_zip(ano)
                salvar_dataframe(df_ano, f"queimadas_{ano}", dados_brutos_dir)
            except Exception as err:
                logger.warning("Falha ao coletar ano %d do INPE: %s", ano, err)
    else:
        logger.info("\n--- [ETAPA 1/5] Coleta: Pula por solicitação (--pular-coleta) ---")

    # 2. Tratamento
    logger.info("\n--- [ETAPA 2/5] Tratamento e Padronização de Dados ---")
    padrao_busca = os.path.join(dados_brutos_dir, "queimadas_*.csv")
    arquivo_tratado = os.path.join(dados_tratados_dir, "queimadas_tratado.csv")

    if os.path.exists(arquivo_tratado) and pular_coleta:
        logger.info("Utilizando arquivo tratado existente: %s", arquivo_tratado)
    else:
        try:
            processar_e_salvar(
                origem_padrao=padrao_busca,
                destino_dir=dados_tratados_dir,
                estado_foco=estado.upper(),
                municipio_foco=municipio.upper(),
            )
        except Exception as err:
            logger.error("Erro durante o tratamento: %s", err)
            if not os.path.exists(arquivo_tratado):
                logger.error("Não foi possível prosseguir sem o arquivo tratado.")
                return False

    # 3. Análise
    logger.info("\n--- [ETAPA 3/5] Análise Estatística e Métricas ---")
    analise_dir = os.path.join(outputs_dir, "analise")
    try:
        executar_analise(
            caminho_entrada=arquivo_tratado,
            diretorio_saida=analise_dir,
            estado_alvo=estado.upper(),
            municipio_alvo=municipio.upper(),
        )
    except Exception as err:
        logger.error("Erro durante a análise estatística: %s", err)
        return False

    # 4. Gráficos
    logger.info("\n--- [ETAPA 4/5] Geração de Gráficos e Visualizações ---")
    graficos_dir = os.path.join(outputs_dir, "graficos")
    try:
        gerar_todos_graficos(
            caminho_csv=arquivo_tratado,
            diretorio_saida=graficos_dir,
            estado=estado.upper(),
            municipio=municipio.upper(),
        )
    except Exception as err:
        logger.error("Erro durante a geração de gráficos: %s", err)
        return False

    # 5. Relatório Técnico Oficial PDF
    logger.info("\n--- [ETAPA 5/5] Compilação do Relatório Técnico Oficial (PDF) ---")
    ranking_csv = os.path.join(analise_dir, "ranking_municipios.csv")
    anual_csv = os.path.join(analise_dir, f"anual_{municipio.lower()}.csv")
    relatorio_pdf = os.path.join(
        outputs_dir, "relatorios", f"relatorio_oficial_{municipio.lower()}.pdf"
    )
    logo_path = os.path.join("assets", "logo.png")

    try:
        gerar_relatorio_pdf(
            caminho_ranking=ranking_csv,
            caminho_anual=anual_csv,
            diretorio_graficos=graficos_dir,
            caminho_saida_pdf=relatorio_pdf,
            municipio=municipio.upper(),
            estado=estado.upper(),
            logo_path=logo_path,
        )
    except Exception as err:
        logger.error("Erro durante a compilação do PDF: %s", err)
        return False

    duracao = time.time() - inicio
    logger.info("=========================================================")
    logger.info("✨ PIPELINE EXECUTADO COM SUCESSO EM %.2f SEGUNDOS!", duracao)
    logger.info("📄 Relatório gerado: %s", relatorio_pdf)
    logger.info("📊 Gráficos disponíveis em: %s", graficos_dir)
    logger.info("=========================================================")
    return True


def parse_args() -> argparse.Namespace:
    """Configura argumentos de linha de comando."""
    parser = argparse.ArgumentParser(
        description="Executa o pipeline completo de dados de queimadas."
    )
    parser.add_argument(
        "--anos",
        nargs="+",
        type=int,
        default=[2020, 2021, 2022, 2024],
        help="Lista de anos a processar.",
    )
    parser.add_argument(
        "--pular-coleta",
        action="store_true",
        help="Pula a etapa de download caso já existam dados locais.",
    )
    parser.add_argument("--estado", type=str, default="PARA", help="Estado alvo da análise.")
    parser.add_argument(
        "--municipio", type=str, default="OBIDOS", help="Município alvo da análise."
    )
    return parser.parse_args()


def main() -> None:
    """Ponto de entrada do script."""
    args = parse_args()
    sucesso = executar_pipeline(
        anos=args.anos, pular_coleta=args.pular_coleta, estado=args.estado, municipio=args.municipio
    )
    if not sucesso:
        sys.exit(1)


if __name__ == "__main__":
    main()
