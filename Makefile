.PHONY: help install dev-install run pipeline test lint format clean

PYTHON := python3
PIP := pip

help:
	@echo "Comandos disponíveis:"
	@echo "  make install      - Instala as dependências básicas"
	@echo "  make dev-install  - Instala dependências de desenvolvimento e testes"
	@echo "  make run          - Inicia o Dashboard Streamlit"
	@echo "  make pipeline     - Executa o pipeline de dados completo (ETL + Análise)"
	@echo "  make test         - Executa a suíte de testes com pytest"
	@echo "  make lint         - Executa o linter ruff"
	@echo "  make format       - Formata o código com ruff"
	@echo "  make clean        - Limpa caches e arquivos temporários"

install:
	$(PIP) install -r requirements.txt

dev-install: install
	$(PIP) install pytest pytest-cov ruff

run:
	streamlit run dashboard/app.py

pipeline:
	$(PYTHON) run_pipeline.py

test:
	pytest tests/ -v

lint:
	ruff check .

format:
	ruff format .

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .ruff_cache htmlcov .coverage
