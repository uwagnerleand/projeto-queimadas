# ==============================================================================
# PROJETO QUEIMADAS - ANÁLISE ESPACIAL E CIÊNCIA DE DADOS EM R
# ==============================================================================
# Script completo para integração de Análise de Dados (Data Wrangling/Estatística)
# e Análise Geoespacial (KDE, Função K de Ripley, Autocorrelação Espacial / LISA)
# ==============================================================================

# 1. Instalação e Carregamento de Pacotes
# ------------------------------------------------------------------------------
pacotes_necessarios <- c(
  "tidyverse",  # dplyr, ggplot2, tidyr, readr, lubridate, purrr
  "sf",         # Manipulação de geometrias vetoriais (Simple Features)
  "spatstat",   # Análise de processos e padrões pontuais (KDE, Ripley's K)
  "spdep",      # Estatística espacial de área (Moran's I, LISA clusters)
  "tmap",       # Mapeamento temático estático e interativo
  "viridis"     # Paletas de cores perceptualmente uniformes para calor/risco
)

instalar_se_ausente <- function(pkg) {
  if (!requireNamespace(pkg, quietly = TRUE)) {
    install.packages(pkg, dependencies = TRUE)
  }
}

# Descomente a linha abaixo caso precise instalar os pacotes no seu ambiente R:
# invisible(lapply(pacotes_necessarios, instalar_se_ausente))

suppressPackageStartupMessages({
  library(tidyverse)
  library(sf)
  library(spatstat)
  library(spdep)
  library(viridis)
})

cat("=========================================================\n")
cat("🚀 INICIANDO ANÁLISE ESPACIAL E DE DADOS COM R\n")
cat("=========================================================\n\n")

# 2. Leitura e Preparação da Base de Dados
# ------------------------------------------------------------------------------
caminho_dados <- file.path("dados", "tratado", "queimadas_tratado.csv")

if (!file.exists(caminho_dados)) {
  stop("Arquivo de dados tratados não encontrado em: ", caminho_dados)
}

cat("📥 Carregando base de dados tratada...\n")
df_queimadas <- read_csv(caminho_dados, show_col_types = FALSE)

# 3. Análise de Dados (Data Wrangling & Estatística Descritiva com Dplyr)
# ------------------------------------------------------------------------------
cat("📊 Executando estatísticas descritivas e agregações temporais...\n")

# A. Resumo anual e taxa de variação YoY por Estado e Município
resumo_anual <- df_queimadas %>%
  group_by(estado, ano) %>%
  summarise(
    total_focos = n(),
    municipios_atingidos = n_distinct(municipio),
    .groups = "drop"
  ) %>%
  group_by(estado) %>%
  mutate(
    variacao_yoy_pct = (total_focos - lag(total_focos)) / lag(total_focos) * 100
  )

print(resumo_anual)

# B. Sazonalidade Mensal Média
sazonalidade_mensal <- df_queimadas %>%
  group_by(mes) %>%
  summarise(
    total_focos = n(),
    media_anual = n() / n_distinct(df_queimadas$ano),
    .groups = "drop"
  ) %>%
  mutate(
    participacao_pct = (total_focos / sum(total_focos)) * 100,
    mes_nome = factor(month.abb[mes], levels = month.abb)
  )

cat("\n📅 Sazonalidade Mensal Consolidada:\n")
print(sazonalidade_mensal)

# 4. Transformação em Objeto Espacial (Simple Features - sf)
# ------------------------------------------------------------------------------
cat("\n🗺️ Convertendo dados tabulares em Objeto Espacial sf (EPSG:4326)...\n")

# Filtrando coordenadas válidas
df_geo_validos <- df_queimadas %>%
  filter(!is.na(latitude), !is.na(longitude)) %>%
  filter(latitude >= -90, latitude <= 90, longitude >= -180, longitude <= 180)

# Criando Simple Feature (WGS84)
sf_focos <- st_as_sf(
  df_geo_validos,
  coords = c("longitude", "latitude"),
  crs = 4326,
  remove = FALSE
)

cat("✓ Total de pontos espaciais validados:", nrow(sf_focos), "\n")

# 5. Análise de Padrão Pontual (Point Pattern Analysis)
# ------------------------------------------------------------------------------
cat("\n🔍 Executando Análise de Padrão Pontual (KDE e Função K de Ripley)...\n")

# Recorte para o município de Óbidos (estudo de caso em profundidade)
sf_obidos <- sf_focos %>% filter(municipio == "OBIDOS")

if (nrow(sf_obidos) > 0) {
  # Conversão para Projeção UTM (Métrica) - SIRGAS 2000 / UTM zone 21S (EPSG:31981)
  # para cálculo de distâncias métricas reais
  sf_obidos_utm <- st_transform(sf_obidos, crs = 31981)
  coords_utm <- st_coordinates(sf_obidos_utm)
  
  # Criação da Janela de Observação (Window)
  janela_bbox <- owin(
    xrange = range(coords_utm[, 1]),
    yrange = range(coords_utm[, 2])
  )
  
  # Criação do Objeto ppp (Point Pattern do spatstat)
  ppp_obidos <- ppp(
    x = coords_utm[, 1],
    y = coords_utm[, 2],
    window = janela_bbox
  )
  
  # A. Estimativa de Densidade Kernel (KDE 2D) com bandwidth adaptativo
  kde_obidos <- density.ppp(ppp_obidos, sigma = bw.ppl(ppp_obidos))
  cat("✓ Densidade Kernel 2D computada com sucesso.\n")
  
  # B. Teste de Agrupamento Espacial (Função K e L de Ripley)
  # Verifica se os focos são agregados (clustering), aleatórios ou regulares
  k_est <- Kest(ppp_obidos, correction = "Ripley")
  cat("✓ Função K de Ripley estimada (Detecção de Clusters Espaciais).\n")
}

# 6. Autocorrelação Espacial de Área (I de Moran & LISA Hotspots)
# ------------------------------------------------------------------------------
cat("\n🌐 Agregando focos por município para Autocorrelação Espacial...\n")

ranking_municipios <- df_queimadas %>%
  filter(estado == "PARA") %>%
  group_by(municipio) %>%
  summarise(
    total_focos = n(),
    latitude_media = mean(latitude, na.rm = TRUE),
    longitude_media = mean(longitude, na.rm = TRUE),
    .groups = "drop"
  )

# Criação de centróides espaciais para matriz de vizinhança k-NN
sf_centroides <- st_as_sf(
  ranking_municipios,
  coords = c("longitude_media", "latitude_media"),
  crs = 4326
)

# Matriz de k-vizinhos mais próximos (k = 5)
coords_mat <- st_coordinates(sf_centroides)
vizinhos_knn <- knearneigh(coords_mat, k = 5)
lista_nb <- knn2nb(vizinhos_knn)
pesos_espaciais <- nb2listw(lista_nb, style = "W")

# Teste Global de Moran
moran_global <- moran.test(ranking_municipios$total_focos, pesos_espaciais)
cat("\n--- Resultado do Teste de Autocorrelação Global de Moran ---\n")
print(moran_global)

# Moran Local (LISA - Local Indicators of Spatial Association)
lisa_local <- localmoran(ranking_municipios$total_focos, pesos_espaciais)
ranking_municipios$lisa_I <- lisa_local[, 1]
ranking_municipios$lisa_pvalor <- lisa_local[, 5]

# Classificação de Quadrantes LISA (Hotspots vs Coldspots)
focos_padronizados <- scale(ranking_municipios$total_focos)
focos_lag <- scale(lag.listw(pesos_espaciais, ranking_municipios$total_focos))

ranking_municipios <- ranking_municipios %>%
  mutate(
    quadrante_lisa = case_when(
      lisa_pvalor > 0.05 ~ "Não Significativo",
      focos_padronizados > 0 & focos_lag > 0 ~ "Alto-Alto (Hotspot)",
      focos_padronizados < 0 & focos_lag < 0 ~ "Baixo-Baixo (Coldspot)",
      focos_padronizados > 0 & focos_lag < 0 ~ "Alto-Baixo (Outlier)",
      focos_padronizados < 0 & focos_lag > 0 ~ "Baixo-Alto (Outlier)"
    )
  )

cat("\n✓ Classificação LISA concluída com sucesso:\n")
table(ranking_municipios$quadrante_lisa)

# 7. Visualizações Científicas com ggplot2
# ------------------------------------------------------------------------------
dir.create(file.path("outputs", "analise_r"), recursive = TRUE, showWarnings = FALSE)

# A. Gráfico 1: Sazonalidade Mensal
p1 <- ggplot(sazonalidade_mensal, aes(x = mes_nome, y = total_focos, fill = total_focos)) +
  geom_col(width = 0.7, show.legend = FALSE) +
  scale_fill_viridis_c(option = "inferno", direction = 1) +
  theme_minimal(base_family = "sans") +
  labs(
    title = "Distribuição Sazonal de Focos de Queimadas",
    subtitle = "Agregação mensal acumulada (2020 - 2024)",
    x = "Mês do Ano",
    y = "Quantidade Total de Focos Detectados"
  ) +
  theme(
    plot.title = element_text(face = "bold", size = 14, color = "#0f172a"),
    plot.subtitle = element_text(color = "#64748b", size = 11),
    panel.grid.minor = element_blank()
  )

ggsave(
  filename = file.path("outputs", "analise_r", "r_sazonalidade_mensal.png"),
  plot = p1, width = 9, height = 5, dpi = 300
)

# B. Gráfico 2: Dispersão Espacial e Densidade de Focos
p2 <- ggplot(df_geo_validos %>% sample_n(min(nrow(df_geo_validos), 20000)), 
             aes(x = longitude, y = latitude)) +
  stat_density_2d(aes(fill = after_stat(level)), geom = "polygon", alpha = 0.6) +
  scale_fill_viridis_c(option = "magma", name = "Densidade") +
  geom_point(color = "#ef4444", size = 0.3, alpha = 0.2) +
  coord_quickmap() +
  theme_dark() +
  labs(
    title = "Mapeamento e Densidade Espacial 2D de Queimadas",
    subtitle = "Pontos geoespaciais e estimativa de densidade Kernel (KDE)",
    x = "Longitude (WGS84)",
    y = "Latitude (WGS84)"
  ) +
  theme(
    plot.title = element_text(face = "bold", size = 14, color = "white"),
    plot.subtitle = element_text(color = "#cbd5e1", size = 11)
  )

ggsave(
  filename = file.path("outputs", "analise_r", "r_mapa_densidade_espacial.png"),
  plot = p2, width = 9, height = 7, dpi = 300
)

# 8. Exportação dos Resultados Espaciais
# ------------------------------------------------------------------------------
cat("\n💾 Exportando resultados espaciais integrados...\n")

# Exporta tabela com clusters LISA
write_csv(
  ranking_municipios,
  file.path("outputs", "analise_r", "r_clusters_lisa_municipios.csv")
)

# Exporta Simple Feature em GeoPackage (Padrão OGC aberto)
st_write(
  sf_focos %>% head(5000),
  file.path("outputs", "analise_r", "focos_amostra.gpkg"),
  delete_dsn = TRUE,
  quiet = TRUE
)

cat("\n=========================================================\n")
cat("✨ ANÁLISE ESPACIAL E DE DADOS EM R CONCLUÍDA COM SUCESSO!\n")
cat("📁 Artefatos salvos em: outputs/analise_r/\n")
cat("=========================================================\n")
