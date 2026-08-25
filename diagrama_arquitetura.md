# 📐 Arquitetura do Sistema – Projeto Queimadas

Este documento detalha o fluxo arquitetural e o pipeline de engenharia de dados do **Projeto Queimadas**.

---

## 🔄 Fluxograma do Pipeline de Dados (ETL)

```mermaid
flowchart TD
    subgraph Coleta["1. Coleta & Ingestão"]
        INPE["🛰️ Satélite Referência INPE (ZIP/CSV)"] --> Download["scripts/coleta.py"]
        API["🌐 APIs Públicas (IBGE / JSON)"] --> Download
        Download --> Raw["📁 dados/bruto/ (CSVs brutos)"]
    end

    subgraph Tratamento["2. Tratamento & Normalização"]
        Raw --> Clean["scripts/tratamento.py"]
        Clean --> Normalizacao["- Remoção de Acentos<br>- Conversão Temporal<br>- Validação de Coordenadas Lat/Lon<br>- Desduplicação"]
        Normalizacao --> Treated["📁 dados/tratado/<br>• queimadas_tratado.csv<br>• para.csv<br>• obidos.csv"]
    end

    subgraph Analise["3. Análise Estatística"]
        Treated --> Analytics["scripts/analise.py"]
        Analytics --> Metrics["- Rankings Municipais<br>- Séries Temporais MoM/YoY<br>- Detecção de Eventos Extremos<br>- Representatividade (%)"]
        Metrics --> OutputAnalise["📁 outputs/analise/"]
    end

    subgraph Visualizacao["4. Visualização & Relatórios"]
        OutputAnalise --> Plots["scripts/graficos.py (Matplotlib/Seaborn)"]
        Plots --> GraficosPNG["📁 outputs/graficos/"]
        GraficosPNG --> Report["scripts/relatorio.py (ReportLab)"]
        Report --> PDF["📄 outputs/relatorios/<br>relatorio_oficial_obidos.pdf"]
        
        Treated --> Dashboard["💻 dashboard/app.py (Streamlit)"]
        Dashboard --> WebApp["🌐 Dashboard Interativo<br>• Mapas Folium<br>• Gráficos Altair<br>• Exportação SIG / Excel / CSV"]
    end
```

---

## 📋 Descrição dos Componentes

1. **Coleta de Dados (`scripts/coleta.py`)**:
   - Automatiza o download dos dados anuais do satélite de referência do INPE e de APIs JSON externas com verificação de integridade e streaming em memória.
2. **Tratamento de Dados (`scripts/tratamento.py`)**:
   - Padroniza esquemas de colunas, normaliza textos para padrão ASCII maiúsculo (compatível com GIS e bancos relacionais), trata nulos e gera índices temporais (`ano`, `mes`).
3. **Análise Estatística (`scripts/analise.py`)**:
   - Computa rankings agregados de queimadas por município, calcula variações mensais percentuais (*Month-over-Month*) e identifica períodos com surtos ou quedas atípicas (> 30%).
4. **Geração Gráfica (`scripts/graficos.py`)**:
   - Produz gráficos em alta resolução (300 DPI) para séries históricas, barras mensais com rótulos de valores, comparativos municipais e mapas de calor sazonais.
5. **Relatório Técnico Oficial (`scripts/relatorio.py`)**:
   - Compila automaticamente um documento técnico padrão A4 em formato PDF com papel timbrado, metadados governamentais, tabelas e diagnóstico ambiental.
6. **Dashboard Interativo (`dashboard/app.py`)**:
   - Interface analítica Streamlit com suporte a filtros dinâmicos de Estado/Município/Ano, mapas de calor interativos via Leaflet/Folium, visualizações em Altair e exportação geoespacial (Shapefile, GeoJSON, Excel, CSV).

---

## 🖼️ Diagrama Visual

![Diagrama de Arquitetura do Sistema](arquitetura_pipeline.png)
