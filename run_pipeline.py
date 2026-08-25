#!/usr/bin/env python3
"""
Ponto de entrada conveniente para executar o Pipeline de Dados.

Uso:
    python run_pipeline.py --help
    python run_pipeline.py --pular-coleta
    python run_pipeline.py --estado PARA --municipio OBIDOS
"""

from scripts.pipeline import main

if __name__ == "__main__":
    main()
