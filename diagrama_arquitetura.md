# Diagrama de Arquitetura do Sistema

Este diagrama apresenta o pipeline de dados do sistema:

- Coleta → tratamento → análise → dashboard
- Dados recebidos do INPE ou carregados de arquivo local tratato
- Visualização interativa com Streamlit e exportação para múltiplos formatos

![Diagrama de Arquitetura do Sistema](arquitetura_pipeline.png)

## Descrição do pipeline

1. **Coleta de dados**: scripts/coleta.py obtém dados do INPE ou APIs JSON.
2. **Tratamento de dados**: scripts/tratamento.py padroniza as colunas, datas e nomes de localidades.
3. **Análise de dados**: scripts/analise.py gera métricas, séries temporais e rankings.
4. **Dashboard**: dashboard/app.py exibe filtros, gráficos, mapas e exportação de dados.
