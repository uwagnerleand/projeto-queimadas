"""
Dashboard Interativo de Monitoramento de Queimadas - Projeto Queimadas.

Plataforma analítica geoespacial e temporal desenvolvida com Streamlit,
Plotly, Folium, Altair e ReportLab para suporte à decisão ambiental.
"""

from __future__ import annotations

import io
import os
import tempfile
import zipfile
from io import BytesIO
from typing import Optional

import folium
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st
from folium import plugins
from streamlit_folium import st_folium

# Importações opcionais para SIG
try:
    import geopandas as gpd
    from shapely.geometry import Point

    GEOESPACIAL_DISPONIVEL = True
except (ImportError, OSError):
    gpd = None
    Point = None
    GEOESPACIAL_DISPONIVEL = False

# Caminhos e constantes do sistema
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
DATA_FILE = os.path.join(ROOT_DIR, "dados", "tratado", "queimadas_tratado.csv")
LOGO_FILE = os.path.join(ROOT_DIR, "assets", "logo_q.png")
ICON_FILE = os.path.join(ROOT_DIR, "assets", "icon.png")
INPE_YEARS = [2020, 2021, 2022, 2024]

# ==============================================================================
# CONFIGURAÇÃO DA PÁGINA
# ==============================================================================
st.set_page_config(
    page_title="Projeto Queimadas Pro | Monitoramento Ambiental",
    page_icon=LOGO_FILE if os.path.exists(LOGO_FILE) else "🔥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ==============================================================================
# CSS DESIGN SYSTEM & ÍCONES (FONTAWESOME + BOOTSTRAP ICONS + MODERN GLASSMORPHISM)
# ==============================================================================
st.html("""
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
:root {
    --primary-color: #2563eb;
    --primary-gradient: linear-gradient(135deg, #1d4ed8 0%, #4f46e5 100%);
    --fire-gradient: linear-gradient(135deg, #dc2626 0%, #ea580c 100%);
    --success-gradient: linear-gradient(135deg, #059669 0%, #047857 100%);
    --warning-gradient: linear-gradient(135deg, #d97706 0%, #b45309 100%);
    --card-bg: #ffffff;
    --card-border: #cbd5e1;
    --text-dark: #0f172a;
    --text-light: #ffffff;
    --shadow-soft: 0 4px 20px -2px rgba(15, 23, 42, 0.08);
    --shadow-hover: 0 12px 28px -4px rgba(15, 23, 42, 0.15);
}
html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
}
.stApp {
    background-color: #f8fafc;
    color: #0f172a;
}

/* ==========================================================================
   1. REGRA UNIVERSAL: CAIXAS BRANCAS/CLARAS -> TEXTO PRETO/ESCURO
   ========================================================================== */
/* Títulos e textos gerais da área principal */
.stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6 {
    color: #0f172a !important;
}
.stApp p, .stApp span, .stApp div, .stApp label {
    color: #0f172a;
}

/* Cards de Métricas (Caixa Branca com Borda) */
.glass-card {
    background: #ffffff !important;
    border: 1.5px solid #cbd5e1 !important;
    border-radius: 16px !important;
    padding: 1.35rem 1.5rem !important;
    box-shadow: var(--shadow-soft) !important;
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
}
.glass-card:hover {
    transform: translateY(-3px);
    box-shadow: var(--shadow-hover);
    border-color: #94a3b8 !important;
}
.metric-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.75rem;
}
.metric-title {
    font-size: 0.875rem;
    font-weight: 700;
    color: #475569 !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
.metric-icon-box {
    width: 42px;
    height: 42px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.25rem;
}
.metric-val {
    font-size: 2rem;
    font-weight: 800;
    color: #0f172a !important;
    letter-spacing: -0.02em;
    line-height: 1.2;
}
.metric-footer {
    font-size: 0.85rem;
    margin-top: 0.5rem;
    font-weight: 700;
    display: flex;
    align-items: center;
    gap: 0.35rem;
}
.trend-up { color: #dc2626 !important; }
.trend-down { color: #16a34a !important; }
.trend-neutral { color: #475569 !important; }

/* Abas (Tab List - Fundo Branco com Texto Escuro) */
.stTabs [data-baseweb="tab-list"] {
    background: #ffffff !important;
    border-radius: 14px !important;
    padding: 0.35rem !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06) !important;
    border: 1.5px solid #cbd5e1 !important;
    gap: 0.25rem !important;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 10px !important;
    font-weight: 700 !important;
    color: #334155 !important;
    padding: 0.6rem 1.25rem !important;
    transition: all 0.2s ease !important;
}
/* Aba Ativa: Caixa Escura/Azul com Texto Branco */
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #1d4ed8 0%, #312e81 100%) !important;
    color: #ffffff !important;
    box-shadow: 0 4px 12px rgba(29, 78, 216, 0.3) !important;
}
.stTabs [aria-selected="true"] * {
    color: #ffffff !important;
}

/* Tabelas e Dataframes: Fundo Claro com Texto Preto */
[data-testid="stDataFrame"] {
    background: #ffffff !important;
    border: 1px solid #cbd5e1 !important;
    border-radius: 12px !important;
}
[data-testid="stDataFrame"] * {
    color: #0f172a !important;
}

/* Campos de seleção na área principal (Caixa Branca com Texto Preto) */
.stMainBlockContainer div[data-baseweb="select"] > div {
    background-color: #ffffff !important;
    border: 1.5px solid #cbd5e1 !important;
    color: #0f172a !important;
}
.stMainBlockContainer div[data-baseweb="select"] * {
    color: #0f172a !important;
}

/* ==========================================================================
   2. REGRA UNIVERSAL: CAIXAS PRETAS/ESCURAS -> TEXTO BRANCO
   ========================================================================== */
/* Hero Banner (Caixa Preta/Azul Profundo com Texto Branco) */
.hero-banner {
    background: linear-gradient(135deg, #090d16 0%, #0f172a 60%, #1e1b4b 100%) !important;
    border-radius: 18px;
    padding: 2rem 2.5rem;
    color: #ffffff !important;
    box-shadow: 0 10px 30px rgba(15, 23, 42, 0.25);
    position: relative;
    overflow: hidden;
    margin-bottom: 1.5rem;
    border: 1px solid rgba(255, 255, 255, 0.15);
}
.hero-banner::after {
    content: '';
    position: absolute;
    top: -50%;
    right: -20%;
    width: 400px;
    height: 400px;
    background: radial-gradient(circle, rgba(239, 68, 68, 0.3) 0%, transparent 70%);
    border-radius: 50%;
    pointer-events: none;
}
.hero-title {
    font-size: 2rem;
    font-weight: 800;
    margin: 0;
    letter-spacing: -0.03em;
    display: flex;
    align-items: center;
    gap: 0.75rem;
    color: #ffffff !important;
}
.hero-subtitle {
    font-size: 1rem;
    color: #cbd5e1 !important;
    margin-top: 0.5rem;
    font-weight: 600;
}

/* Barra Lateral (Sidebar - Caixa Escura/Preta com Texto Branco) */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #090d16 0%, #0f172a 100%) !important;
    border-right: 1px solid rgba(255, 255, 255, 0.12) !important;
}
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] b {
    color: #f8fafc !important;
}
section[data-testid="stSidebar"] .stSelectbox label {
    font-weight: 700 !important;
    font-size: 0.92rem !important;
    color: #e2e8f0 !important;
    margin-bottom: 0.25rem !important;
}

/* Caixas de Seleção na Sidebar (Caixa Escura Grafite com Texto Branco) */
section[data-testid="stSidebar"] div[data-baseweb="select"] > div {
    background-color: #1e293b !important;
    border: 1.5px solid #475569 !important;
    border-radius: 10px !important;
    color: #ffffff !important;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.3) !important;
}
section[data-testid="stSidebar"] div[data-baseweb="select"] * {
    color: #ffffff !important;
}
section[data-testid="stSidebar"] div[data-baseweb="select"] svg {
    fill: #cbd5e1 !important;
}

/* Menus Suspensos / Dropdown Popovers (Caixa Escura com Texto Branco) */
div[data-baseweb="popover"] ul,
div[data-baseweb="menu"],
ul[role="listbox"] {
    background-color: #0f172a !important;
    border: 1.5px solid #334155 !important;
    border-radius: 10px !important;
    box-shadow: 0 10px 25px rgba(0,0,0,0.5) !important;
}
div[data-baseweb="popover"] li,
div[data-baseweb="menu"] li,
li[role="option"] {
    color: #f8fafc !important;
    background-color: #0f172a !important;
    font-weight: 500 !important;
}
div[data-baseweb="popover"] li:hover,
div[data-baseweb="menu"] li:hover,
li[role="option"]:hover,
li[aria-selected="true"] {
    background-color: #2563eb !important;
    color: #ffffff !important;
}

/* Botões (Caixas com Gradientes Escuros/Vibrantes com Texto Branco) */
.stDownloadButton > button {
    background: linear-gradient(135deg, #059669 0%, #047857 100%) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 12px !important;
    font-weight: 700 !important;
    padding: 0.75rem 1.5rem !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 4px 14px rgba(5, 150, 105, 0.35) !important;
}
.stDownloadButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(5, 150, 105, 0.45) !important;
}
.stButton > button {
    background: linear-gradient(135deg, #1d4ed8 0%, #1e40af 100%) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 12px !important;
    font-weight: 700 !important;
    padding: 0.75rem 1.5rem !important;
    box-shadow: 0 4px 14px rgba(29, 78, 216, 0.35) !important;
    transition: all 0.2s ease !important;
}
.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(29, 78, 216, 0.45) !important;
}

/* Badges de Alerta (Caixas Claras com Texto Escuro de Alto Contraste) */
.badge {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    padding: 0.35rem 0.85rem;
    border-radius: 9999px;
    font-size: 0.82rem;
    font-weight: 800;
    letter-spacing: 0.02em;
}
.badge-critical { background: #fee2e2 !important; color: #7f1d1d !important; border: 1.5px solid #fca5a5 !important; }
.badge-high { background: #ffedd5 !important; color: #7c2d12 !important; border: 1.5px solid #fdba74 !important; }
.badge-medium { background: #fef3c7 !important; color: #78350f !important; border: 1.5px solid #fcd34d !important; }
.badge-low { background: #dcfce7 !important; color: #14532d !important; border: 1.5px solid #86efac !important; }
</style>
""")


# ==============================================================================
# FUNÇÕES DE EXPORTAÇÃO SIG & TABULARES
# ==============================================================================


def preparar_exportacao(df: pd.DataFrame) -> pd.DataFrame:
    """Prepara colunas temporais e de texto para exportação em formatos compatíveis."""
    df_export = df.copy()
    geometry_col = None
    if GEOESPACIAL_DISPONIVEL and isinstance(df_export, gpd.GeoDataFrame):
        geometry_col = df_export.geometry.name

    for col in df_export.columns:
        if col != geometry_col and pd.api.types.is_datetime64_any_dtype(df_export[col]):
            df_export[col] = df_export[col].dt.strftime("%Y-%m-%d %H:%M:%S")

    return df_export


def criar_geodataframe(df: pd.DataFrame):
    """Gera GeoDataFrame com coordenadas CRS EPSG:4326."""
    if not GEOESPACIAL_DISPONIVEL:
        raise ValueError("GeoPandas não instalado no ambiente.")

    df_geo = preparar_exportacao(df).copy()
    if "latitude" not in df_geo.columns or "longitude" not in df_geo.columns:
        raise ValueError("Colunas de latitude e longitude ausentes.")

    df_geo["latitude"] = pd.to_numeric(df_geo["latitude"], errors="coerce")
    df_geo["longitude"] = pd.to_numeric(df_geo["longitude"], errors="coerce")
    df_geo = df_geo.dropna(subset=["latitude", "longitude"])
    df_geo = df_geo[
        (df_geo["latitude"].between(-90, 90)) & (df_geo["longitude"].between(-180, 180))
    ]

    geometry = [Point(lon, lat) for lon, lat in zip(df_geo.longitude, df_geo.latitude)]
    gdf = gpd.GeoDataFrame(df_geo, geometry=geometry, crs="EPSG:4326")
    return gdf


def exportar_shapefile_zip(gdf) -> Optional[bytes]:
    """Exporta GeoDataFrame em arquivo ZIP contendo o Shapefile (.shp, .shx, .dbf, .prj)."""
    if gdf is None or gdf.empty:
        return None
    gdf_exp = preparar_exportacao(gdf)
    with tempfile.TemporaryDirectory() as temp_dir:
        shp_path = os.path.join(temp_dir, "queimadas.shp")
        gdf_exp.to_file(shp_path, driver="ESRI Shapefile", encoding="utf-8")
        zip_buf = BytesIO()
        with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for fname in os.listdir(temp_dir):
                zf.write(os.path.join(temp_dir, fname), fname)
        zip_buf.seek(0)
        return zip_buf.getvalue()


def exportar_geojson(gdf) -> Optional[bytes]:
    """Exporta GeoDataFrame em GeoJSON codificado em UTF-8."""
    if gdf is None or gdf.empty:
        return None
    gdf_exp = preparar_exportacao(gdf)
    return gdf_exp.to_json(indent=2).encode("utf-8")


def exportar_csv(df: pd.DataFrame) -> bytes:
    """Exporta DataFrame em CSV compatível com Excel UTF-8 BOM."""
    df_exp = preparar_exportacao(df)
    buf = BytesIO()
    df_exp.to_csv(buf, index=False, encoding="utf-8-sig")
    buf.seek(0)
    return buf.getvalue()


def exportar_excel(df: pd.DataFrame, ranking: pd.DataFrame) -> bytes:
    """Gera planilha Excel (.xlsx) com múltiplas abas formatadas."""
    df_exp = preparar_exportacao(df)
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df_exp.to_excel(writer, sheet_name="Focos_Filtrados", index=False)
        if ranking is not None and not ranking.empty:
            ranking.to_excel(writer, sheet_name="Ranking_Estadual", index=False)
    buf.seek(0)
    return buf.getvalue()


# ==============================================================================
# CARREGAMENTO E INGESTÃO DE DADOS COM CACHE
# ==============================================================================


def carregar_dados_inpe_ano(ano: int) -> pd.DataFrame:
    """Baixa e extrai dados do INPE diretamente da nuvem."""
    url = f"https://dataserver-coids.inpe.br/queimadas/queimadas/focos/csv/anual/Brasil_sat_ref/focos_br_ref_{ano}.zip"
    headers = {"User-Agent": "ProjetoQueimadas/1.0"}
    resp = requests.get(url, headers=headers, timeout=60)
    resp.raise_for_status()

    with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
        csv_name = next(f for f in zf.namelist() if f.lower().endswith(".csv"))
        try:
            with zf.open(csv_name) as f:
                df = pd.read_csv(f)
        except Exception:
            with zf.open(csv_name) as f:
                df = pd.read_csv(f, encoding="latin1")

    df.columns = df.columns.str.lower().str.strip()
    return df


@st.cache_data(show_spinner="Carregando e indexando dados de queimadas...")
def carregar_dados() -> pd.DataFrame:
    """Carrega dados tratados locais ou aciona download direto com fallback."""
    df = None
    if os.path.exists(DATA_FILE):
        try:
            df_temp = pd.read_csv(DATA_FILE, low_memory=False)
            if "data" in df_temp.columns and len(df_temp) > 100:
                df = df_temp
        except Exception:
            df = None

    if df is None:
        dfs = []
        for ano in INPE_YEARS:
            try:
                dfs.append(carregar_dados_inpe_ano(ano))
            except Exception:
                pass
        df = pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()

    df = df.rename(columns={"lat": "latitude", "lon": "longitude", "long": "longitude"})

    col_data = (
        "datahora" if "datahora" in df.columns else "data" if "data" in df.columns else "data_pas"
    )
    df["data"] = pd.to_datetime(df[col_data], errors="coerce")
    df = df.dropna(subset=["data"])

    df["mes"] = df["data"].dt.month
    df["ano"] = df["data"].dt.year

    if "estado" in df.columns:
        df["estado"] = df["estado"].astype(str).str.upper().str.strip()
    if "municipio" in df.columns:
        df["municipio"] = df["municipio"].astype(str).str.upper().str.strip()
    if "bioma" in df.columns:
        df["bioma"] = df["bioma"].astype(str).str.upper().str.strip()

    return df


try:
    df_geral = carregar_dados()
except Exception as exc:
    st.error("Não foi possível carregar os dados de monitoramento.")
    st.exception(exc)
    st.stop()


# ==============================================================================
# SIDEBAR - FILTROS DINÂMICOS & CONTROLES
# ==============================================================================
with st.sidebar:
    st.html("""
    <div style="text-align: center; padding: 1rem 0;">
        <h2 style="color: white; margin: 0; font-size: 1.4rem; font-weight: 800; display: flex; align-items: center; justify-content: center; gap: 0.5rem;">
            <i class="fa-solid fa-fire-flame-curved" style="color: #f97316;"></i> QUEIMADAS <span style="color: #38bdf8; font-size: 0.8rem; background: rgba(56, 189, 248, 0.2); padding: 2px 8px; border-radius: 8px;">PRO</span>
        </h2>
        <p style="color: #94a3b8; font-size: 0.8rem; margin-top: 4px;">Monitoramento Satelital INPE</p>
    </div>
    <hr style="border-color: rgba(255,255,255,0.1); margin: 0.5rem 0 1.25rem 0;">
    """)

    st.markdown("### <i class='fa-solid fa-sliders' style='color: #38bdf8;'></i> Filtros de Consulta", unsafe_allow_html=True)

    # 1. Filtro de Estado
    estados_disponiveis = sorted(df_geral["estado"].unique())
    estado_default_idx = estados_disponiveis.index("PARA") if "PARA" in estados_disponiveis else 0
    estado_sel = st.selectbox("Estado Federativo (UF)", estados_disponiveis, index=estado_default_idx)

    df_estado = df_geral[df_geral["estado"] == estado_sel]

    # 2. Filtro de Município
    municipios_disponiveis = sorted(df_estado["municipio"].unique())
    mun_default_idx = (
        municipios_disponiveis.index("OBIDOS") if "OBIDOS" in municipios_disponiveis else 0
    )
    municipio_sel = st.selectbox("Município Alvo", municipios_disponiveis, index=mun_default_idx)

    # 3. Filtro de Ano
    anos_disponiveis = sorted(df_geral["ano"].unique(), reverse=True)
    ano_sel = st.selectbox("Ano de Referência", anos_disponiveis, index=0)

    st.html("<hr style='border-color: rgba(255,255,255,0.1); margin: 1rem 0;'>")

    # Botão de Ação Rápida
    if st.button("Atualizar / Limpar Cache", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    # Informações Técnicas na Sidebar
    st.html("""
    <div style="background: #1e293b; padding: 1rem; border-radius: 12px; margin-top: 1rem; border: 1.5px solid #334155;">
        <p style="font-size: 0.8rem; color: #f8fafc; margin: 0;"><i class="fa-solid fa-satellite-dish" style="color: #38bdf8;"></i> <b style="color: #ffffff;">Fonte:</b> INPE / BDQueimadas</p>
        <p style="font-size: 0.8rem; color: #f8fafc; margin: 6px 0 0 0;"><i class="fa-solid fa-clock" style="color: #38bdf8;"></i> <b style="color: #ffffff;">Atualização:</b> Satélite de Ref.</p>
        <p style="font-size: 0.8rem; color: #f8fafc; margin: 6px 0 0 0;"><i class="fa-solid fa-shield-halved" style="color: #10b981;"></i> <b style="color: #ffffff;">Status:</b> Operacional</p>
    </div>
    """)


# Filtragem dos conjuntos de dados
df_filtrado = df_geral[
    (df_geral["estado"] == estado_sel)
    & (df_geral["municipio"] == municipio_sel)
    & (df_geral["ano"] == ano_sel)
]
df_estado_ano = df_geral[(df_geral["estado"] == estado_sel) & (df_geral["ano"] == ano_sel)]
df_municipio_historico = df_geral[
    (df_geral["estado"] == estado_sel) & (df_geral["municipio"] == municipio_sel)
]


# ==============================================================================
# HERO HEADER PRINCIPAL
# ==============================================================================
total_focos = len(df_filtrado)
total_estado = len(df_estado_ano)
percentual_estado = (total_focos / total_estado * 100) if total_estado > 0 else 0.0

# Classificação de Risco
if total_focos > 2000:
    badge_html = "<span class='badge badge-critical'><i class='fa-solid fa-triangle-exclamation'></i> Risco Crítico / Alerta Máximo</span>"
elif total_focos > 500:
    badge_html = "<span class='badge badge-high'><i class='fa-solid fa-fire-flame-curved'></i> Risco Elevado</span>"
elif total_focos > 100:
    badge_html = "<span class='badge badge-medium'><i class='fa-solid fa-circle-exclamation'></i> Risco Moderado</span>"
else:
    badge_html = "<span class='badge badge-low'><i class='fa-solid fa-circle-check'></i> Risco Controlado</span>"

st.html(f"""
<div class="hero-banner">
    <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 1rem;">
        <div>
            <div class="hero-title">
                <i class="fa-solid fa-fire-burner" style="color: #f97316;"></i> Monitoramento de Queimadas
            </div>
            <div class="hero-subtitle">
                <i class="fa-solid fa-location-dot" style="color: #38bdf8;"></i> <b>{municipio_sel}</b>, {estado_sel} &nbsp;|&nbsp;
                <i class="fa-solid fa-calendar-days"></i> Ano Base: <b>{ano_sel}</b>
            </div>
        </div>
        <div>
            {badge_html}
        </div>
    </div>
</div>
""")


# ==============================================================================
# CARDS DE MÉTRICAS EXECUTIVAS
# ==============================================================================
# Cálculo de variação YoY em relação ao ano anterior
ano_anterior = ano_sel - 1
focos_ano_ant = len(df_municipio_historico[df_municipio_historico["ano"] == ano_anterior])
if focos_ano_ant > 0:
    var_yoy = ((total_focos - focos_ano_ant) / focos_ano_ant) * 100
    yoy_text = f"{'+' if var_yoy > 0 else ''}{var_yoy:.1f}% vs {ano_anterior}"
    yoy_class = "trend-up" if var_yoy > 0 else "trend-down"
    yoy_icon = "fa-arrow-trend-up" if var_yoy > 0 else "fa-arrow-trend-down"
else:
    yoy_text = "Sem base prévia"
    yoy_class = "trend-neutral"
    yoy_icon = "fa-minus"

# Mês com maior incidência
if not df_filtrado.empty:
    pico_mes_num = df_filtrado.groupby("mes").size().idxmax()
    meses_nomes = {
        1: "Janeiro",
        2: "Fevereiro",
        3: "Março",
        4: "Abril",
        5: "Maio",
        6: "Junho",
        7: "Julho",
        8: "Agosto",
        9: "Setembro",
        10: "Outubro",
        11: "Novembro",
        12: "Dezembro",
    }
    pico_mes_nome = meses_nomes.get(pico_mes_num, "N/A")
    pico_focos = df_filtrado.groupby("mes").size().max()
else:
    pico_mes_nome = "N/A"
    pico_focos = 0

st.html(f"""
<div class="metric-grid">
    <div class="glass-card">
        <div class="metric-header">
            <span class="metric-title">Focos Detectados</span>
            <div class="metric-icon-box" style="background: #fee2e2; color: #dc2626;">
                <i class="fa-solid fa-fire"></i>
            </div>
        </div>
        <div class="metric-val">{total_focos:,}</div>
        <div class="metric-footer {yoy_class}">
            <i class="fa-solid {yoy_icon}"></i> {yoy_text}
        </div>
    </div>
    <div class="glass-card">
        <div class="metric-header">
            <span class="metric-title">Pico Sazonal</span>
            <div class="metric-icon-box" style="background: #ffedd5; color: #ea580c;">
                <i class="fa-solid fa-chart-line"></i>
            </div>
        </div>
        <div class="metric-val">{pico_mes_nome}</div>
        <div class="metric-footer trend-neutral">
            <i class="fa-solid fa-circle-info"></i> {pico_focos:,} focos no mês crítico
        </div>
    </div>
    <div class="glass-card">
        <div class="metric-header">
            <span class="metric-title">Participação Estadual</span>
            <div class="metric-icon-box" style="background: #e0e7ff; color: #4338ca;">
                <i class="fa-solid fa-chart-pie"></i>
            </div>
        </div>
        <div class="metric-val">{percentual_estado:.2f}%</div>
        <div class="metric-footer trend-neutral">
            <i class="fa-solid fa-map-location-dot"></i> Total de {total_estado:,} no {estado_sel}
        </div>
    </div>
    <div class="glass-card">
        <div class="metric-header">
            <span class="metric-title">Média Mensal</span>
            <div class="metric-icon-box" style="background: #dcfce7; color: #16a34a;">
                <i class="fa-solid fa-calculator"></i>
            </div>
        </div>
        <div class="metric-val">{(total_focos / 12.0):,.1f}</div>
        <div class="metric-footer trend-neutral">
            <i class="fa-solid fa-calendar-check"></i> Focos/mês no período
        </div>
    </div>
</div>
""")


# ==============================================================================
# ABAS DE NAVEGAÇÃO E ANÁLISE INTERATIVA
# ==============================================================================
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
    [
        "Visão Geral & KPIs",
        "Análise Temporal & Sazonal",
        "GeoAnalytics & Mapa",
        "Ranking & Comparativos",
        "Base de Dados & SIG",
        "Relatório Oficial PDF",
    ]
)


# ------------------------------------------------------------------------------
# TAB 1: VISÃO GERAL & KPIS ESTRATÉGICOS
# ------------------------------------------------------------------------------
with tab1:
    col_g1, col_g2 = st.columns([3, 2])

    with col_g1:
        st.markdown("#### <i class='fa-solid fa-chart-column' style='color: #2563eb;'></i> Distribuição Mensal de Focos de Calor", unsafe_allow_html=True)
        if not df_filtrado.empty:
            df_mes = df_filtrado.groupby("mes").size().reset_index(name="focos")
            meses_map = {
                1: "Jan",
                2: "Fev",
                3: "Mar",
                4: "Abr",
                5: "Mai",
                6: "Jun",
                7: "Jul",
                8: "Ago",
                9: "Set",
                10: "Out",
                11: "Nov",
                12: "Dez",
            }
            df_mes_full = (
                pd.DataFrame({"mes": list(range(1, 13))})
                .merge(df_mes, on="mes", how="left")
                .fillna({"focos": 0})
            )
            df_mes_full["mes_nome"] = df_mes_full["mes"].map(meses_map)

            fig_bar = px.bar(
                df_mes_full,
                x="mes_nome",
                y="focos",
                text="focos",
                labels={"mes_nome": "Mês", "focos": "Quantidade de Focos"},
                color="focos",
                color_continuous_scale="YlOrRd",
            )
            fig_bar.update_traces(
                textposition="outside",
                texttemplate="%{text:,.0f}",
                marker_line_width=0,
                opacity=0.9,
            )
            fig_bar.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                height=360,
                margin=dict(l=10, r=10, t=25, b=10),
                coloraxis_showscale=False,
                xaxis=dict(showgrid=False, tickfont=dict(size=12, color="#334155")),
                yaxis=dict(
                    showgrid=True, gridcolor="#f1f5f9", tickfont=dict(size=11, color="#64748b")
                ),
            )
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("Nenhum dado registrado para o período selecionado.")

    with col_g2:
        st.markdown("#### <i class='fa-solid fa-gauge-high' style='color: #ea580c;'></i> Indicador de Intensidade e Risco", unsafe_allow_html=True)
        max_gauge = max(total_focos * 1.5, 1000)
        fig_gauge = go.Figure(
            go.Indicator(
                mode="gauge+number",
                value=total_focos,
                domain={"x": [0, 1], "y": [0, 1]},
                title={
                    "text": f"Focos em {municipio_sel}",
                    "font": {"size": 14, "color": "#475569"},
                },
                gauge={
                    "axis": {"range": [None, max_gauge], "tickwidth": 1, "tickcolor": "#94a3b8"},
                    "bar": {"color": "#ef4444"},
                    "bgcolor": "white",
                    "borderwidth": 1,
                    "bordercolor": "#e2e8f0",
                    "steps": [
                        {"range": [0, max_gauge * 0.3], "color": "#dcfce7"},
                        {"range": [max_gauge * 0.3, max_gauge * 0.7], "color": "#fef3c7"},
                        {"range": [max_gauge * 0.7, max_gauge], "color": "#fee2e2"},
                    ],
                },
            )
        )
        fig_gauge.update_layout(
            height=360, margin=dict(l=20, r=20, t=40, b=20), paper_bgcolor="rgba(0,0,0,0)"
        )
        st.plotly_chart(fig_gauge, use_container_width=True)

    # Diagnóstico e Destaques Ambientais
    st.html("""
    <div style="background: white; border: 1.5px solid #cbd5e1; border-radius: 14px; padding: 1.25rem 1.5rem; margin-top: 1rem;">
        <h4 style="margin: 0 0 0.5rem 0; color: #0f172a; font-size: 1.05rem;">
            <i class="fa-solid fa-bullhorn" style="color: #2563eb;"></i> Diagnóstico Rápido de Gestão Ambiental
        </h4>
        <p style="margin: 0; color: #334155; font-size: 0.9rem; line-height: 1.6;">
            Os registros indicam que a maior concentração de focos no município ocorre no período do segundo semestre (estiagem amazônica).
            Recomenda-se o fortalecimento preventivo das brigadas de incêndio e monitoramento contínuo das áreas de maior densidade de calor.
        </p>
    </div>
    """)


# ------------------------------------------------------------------------------
# TAB 2: ANÁLISE TEMPORAL & SAZONALIDADE
# ------------------------------------------------------------------------------
with tab2:
    st.markdown("#### <i class='fa-solid fa-chart-line' style='color: #2563eb;'></i> Série Temporal Histórica de Queimadas", unsafe_allow_html=True)

    col_t1, col_t2 = st.columns([3, 1])
    with col_t1:
        escopo_temporal = st.radio(
            "Visualização da Série:",
            ["Série Multianual Completa (2020 a 2024)", f"Apenas o Ano Selecionado ({ano_sel})"],
            horizontal=True,
        )

    if escopo_temporal.startswith("Série Multianual"):
        df_serie = df_municipio_historico.groupby(["ano", "mes"]).size().reset_index(name="focos")
    else:
        df_serie = df_filtrado.groupby(["ano", "mes"]).size().reset_index(name="focos")

    if not df_serie.empty:
        df_serie["data"] = pd.to_datetime(
            df_serie["ano"].astype(str) + "-" + df_serie["mes"].astype(str).str.zfill(2) + "-01"
        )
        df_serie = df_serie.sort_values("data")

        # Gráfico Interativo com Range Slider
        fig_time = px.area(
            df_serie,
            x="data",
            y="focos",
            labels={"data": "Data", "focos": "Focos de Calor"},
            color_discrete_sequence=["#3b82f6"],
        )
        fig_time.update_traces(
            line=dict(width=2.5, color="#2563eb"), fillcolor="rgba(59, 130, 246, 0.15)"
        )
        fig_time.update_layout(
            height=380,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(
                rangeselector=dict(
                    buttons=list(
                        [
                            dict(count=6, label="6m", step="month", stepmode="backward"),
                            dict(count=1, label="1 ano", step="year", stepmode="backward"),
                            dict(step="all", label="Tudo"),
                        ]
                    )
                ),
                rangeslider=dict(visible=True, thickness=0.08),
                type="date",
            ),
            margin=dict(l=10, r=10, t=10, b=10),
        )
        st.plotly_chart(fig_time, use_container_width=True)

    # Comparativo Interanual Mês a Mês
    st.markdown("#### <i class='fa-solid fa-arrows-split-up-and-left' style='color: #7c3aed;'></i> Comparativo de Sazonalidade por Ano (Mês a Mês)", unsafe_allow_html=True)
    if not df_municipio_historico.empty:
        df_sazonal = df_municipio_historico.groupby(["ano", "mes"]).size().reset_index(name="focos")
        meses_labels = {
            1: "Jan",
            2: "Fev",
            3: "Mar",
            4: "Abr",
            5: "Mai",
            6: "Jun",
            7: "Jul",
            8: "Ago",
            9: "Set",
            10: "Out",
            11: "Nov",
            12: "Dez",
        }
        df_sazonal["mes_nome"] = df_sazonal["mes"].map(meses_labels)

        fig_comp = px.line(
            df_sazonal,
            x="mes_nome",
            y="focos",
            color="ano",
            markers=True,
            labels={"mes_nome": "Mês", "focos": "Focos", "ano": "Ano"},
            color_discrete_sequence=px.colors.qualitative.Bold,
        )
        fig_comp.update_layout(
            height=360,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=10, r=10, t=20, b=10),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        st.plotly_chart(fig_comp, use_container_width=True)


# ------------------------------------------------------------------------------
# TAB 3: GEOANALYTICS & MAPA INTERATIVO AVANÇADO
# ------------------------------------------------------------------------------
with tab3:
    st.markdown("#### <i class='fa-solid fa-map-location-dot' style='color: #059669;'></i> Mapeamento Espacial Interativo", unsafe_allow_html=True)

    df_mapa = df_filtrado.dropna(subset=["latitude", "longitude"])

    if not df_mapa.empty:
        col_m1, col_m2 = st.columns([4, 1])
        with col_m2:
            estilo_mapa = st.selectbox(
                "Camada de Fundo:",
                ["CartoDB Positron (Claro)", "OpenStreetMap", "Satélite (Esri WorldImagery)"],
            )
            tipo_visualizacao = st.radio(
                "Visualização:", ["Mapa de Calor (HeatMap)", "Pontos Agrupados (Cluster)"]
            )

        # Configurar tiles
        if estilo_mapa == "Satélite (Esri WorldImagery)":
            tiles_url = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
            attr = "Esri WorldImagery"
        elif estilo_mapa == "OpenStreetMap":
            tiles_url = "OpenStreetMap"
            attr = None
        else:
            tiles_url = "CartoDB positron"
            attr = None

        centro_lat = float(df_mapa["latitude"].mean())
        centro_lon = float(df_mapa["longitude"].mean())

        m = folium.Map(location=[centro_lat, centro_lon], zoom_start=9, tiles=tiles_url, attr=attr)

        plugins.Fullscreen(position="topright").add_to(m)
        plugins.MiniMap(toggle_display=True).add_to(m)

        if tipo_visualizacao.startswith("Mapa de Calor"):
            heat_data = df_mapa[["latitude", "longitude"]].values.tolist()
            plugins.HeatMap(
                heat_data,
                radius=14,
                blur=12,
                max_zoom=10,
                gradient={0.2: "blue", 0.4: "lime", 0.6: "yellow", 0.8: "orange", 1: "red"},
            ).add_to(m)
        else:
            cluster = plugins.MarkerCluster().add_to(m)
            # Limitar pontos no cluster se for excessivo para melhor performance
            amostra_mapa = df_mapa.head(2000)
            for _, row in amostra_mapa.iterrows():
                folium.CircleMarker(
                    location=[row["latitude"], row["longitude"]],
                    radius=5,
                    color="#dc2626",
                    fill=True,
                    fill_color="#ef4444",
                    fill_opacity=0.7,
                    popup=f"<b>Data:</b> {str(row['data'])[:10]}<br><b>Município:</b> {municipio_sel}<br><b>Lat:</b> {row['latitude']:.4f}<br><b>Lon:</b> {row['longitude']:.4f}",
                ).add_to(cluster)

        with col_m1:
            st_folium(m, width="100%", height=560)
    else:
        st.warning("Sem coordenadas espaciais válidas para o filtro aplicado.")


# ------------------------------------------------------------------------------
# TAB 4: RANKING & COMPARATIVOS MUNICIPAIS
# ------------------------------------------------------------------------------
with tab4:
    st.markdown(f"#### <i class='fa-solid fa-trophy' style='color: #d97706;'></i> Ranking de Queimadas no Estado do {estado_sel} ({ano_sel})", unsafe_allow_html=True)

    ranking_estado = df_estado_ano.groupby("municipio").size().reset_index(name="focos")
    ranking_estado = ranking_estado.sort_values("focos", ascending=False).reset_index(drop=True)

    if not ranking_estado.empty:
        ranking_estado["posicao"] = ranking_estado.index + 1
        top10_df = ranking_estado.head(10).copy()

        # Destaque do município selecionado
        if municipio_sel in ranking_estado["municipio"].values:
            pos_atual = int(
                ranking_estado[ranking_estado["municipio"] == municipio_sel]["posicao"].values[0]
            )
            focos_atual = int(
                ranking_estado[ranking_estado["municipio"] == municipio_sel]["focos"].values[0]
            )
            st.html(f"""
            <div style="background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%); border-radius: 12px; padding: 1rem 1.5rem; margin-bottom: 1.25rem; border: 1.5px solid #bfdbfe; display: flex; align-items: center; gap: 1.25rem;">
                <div style="font-size: 2.2rem; color: #d97706;"><i class="fa-solid fa-trophy"></i></div>
                <div>
                    <span style="font-size: 1.1rem; font-weight: 800; color: #1e40af;">
                        {municipio_sel} está na posição #{pos_atual} no ranking estadual com {focos_atual:,} focos detectados.
                    </span>
                    <p style="margin: 0; color: #1e3a8a; font-size: 0.88rem; font-weight: 600;">Representa {percentual_estado:.2f}% de todos os focos no estado do {estado_sel} em {ano_sel}.</p>
                </div>
            </div>
            """)

        col_r1, col_r2 = st.columns([3, 2])
        with col_r1:
            fig_rank = px.bar(
                top10_df.sort_values("focos", ascending=True),
                x="focos",
                y="municipio",
                orientation="h",
                text="focos",
                labels={"focos": "Focos de Calor", "municipio": "Município"},
                color="focos",
                color_continuous_scale="OrRd",
            )
            fig_rank.update_traces(textposition="outside", texttemplate="%{text:,.0f}")
            fig_rank.update_layout(
                height=400,
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                coloraxis_showscale=False,
                margin=dict(l=10, r=10, t=10, b=10),
            )
            st.plotly_chart(fig_rank, use_container_width=True)

        with col_r2:
            st.markdown("##### <i class='fa-solid fa-ranking-star' style='color: #d97706;'></i> Top 10 Municípios", unsafe_allow_html=True)
            top10_display = top10_df[["posicao", "municipio", "focos"]].copy()
            top10_display.columns = ["Posição", "Município", "Focos"]
            st.dataframe(top10_display, hide_index=True, use_container_width=True, height=360)


# ------------------------------------------------------------------------------
# TAB 5: CENTRAL DE DADOS & EXPORTAÇÃO SIG
# ------------------------------------------------------------------------------
with tab5:
    st.markdown("#### <i class='fa-solid fa-database' style='color: #2563eb;'></i> Base de Dados Completa e Exportação", unsafe_allow_html=True)
    st.info(
        f"Foram encontrados **{len(df_filtrado):,}** registros para {municipio_sel} ({estado_sel}) no ano {ano_sel}."
    )

    st.dataframe(df_filtrado, height=380, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown("### <i class='fa-solid fa-download' style='color: #059669;'></i> Central de Downloads Multiformato", unsafe_allow_html=True)

    col_e1, col_e2 = st.columns(2)

    with col_e1:
        st.markdown("##### <i class='fa-solid fa-file-lines' style='color: #2563eb;'></i> Formatos Tabulares", unsafe_allow_html=True)
        csv_bytes = exportar_csv(df_filtrado)
        st.download_button(
            label="Baixar em formato CSV (UTF-8)",
            data=csv_bytes,
            file_name=f"queimadas_{municipio_sel.lower()}_{ano_sel}.csv",
            mime="text/csv",
            use_container_width=True,
        )

        excel_bytes = exportar_excel(
            df_filtrado, ranking_estado if not ranking_estado.empty else pd.DataFrame()
        )
        st.download_button(
            label="Baixar Planilha Excel (.xlsx)",
            data=excel_bytes,
            file_name=f"queimadas_{municipio_sel.lower()}_{ano_sel}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

    with col_e2:
        st.markdown("##### <i class='fa-solid fa-earth-americas' style='color: #059669;'></i> Formatos Geoespaciais (SIG / GIS)", unsafe_allow_html=True)
        if GEOESPACIAL_DISPONIVEL:
            try:
                gdf_export = criar_geodataframe(df_filtrado)
                geojson_bytes = exportar_geojson(gdf_export)
                if geojson_bytes:
                    st.download_button(
                        label="Baixar GeoJSON (QGIS / WebGIS)",
                        data=geojson_bytes,
                        file_name=f"queimadas_{municipio_sel.lower()}_{ano_sel}.geojson",
                        mime="application/geo+json",
                        use_container_width=True,
                    )

                shp_bytes = exportar_shapefile_zip(gdf_export)
                if shp_bytes:
                    st.download_button(
                        label="Baixar Shapefile Compactado (.ZIP)",
                        data=shp_bytes,
                        file_name=f"queimadas_{municipio_sel.lower()}_{ano_sel}.zip",
                        mime="application/zip",
                        use_container_width=True,
                    )
            except Exception as e:
                st.warning(f"Exportação SIG indisponível: {e}")
        else:
            st.info("Módulos de exportação SIG (GeoJSON / Shapefile) requerem Geopandas.")


# ------------------------------------------------------------------------------
# TAB 6: RELATÓRIO TÉCNICO OFICIAL PDF
# ------------------------------------------------------------------------------
with tab6:
    st.markdown("#### <i class='fa-solid fa-file-pdf' style='color: #dc2626;'></i> Relatório Técnico Oficial de Monitoramento (PDF)", unsafe_allow_html=True)
    st.markdown("""
    Gere e baixe automaticamente um relatório técnico em padrão oficial com capa governamental,
    introdução ambiental, análises descritivas, gráficos de alta resolução (300 DPI) e recomendações técnicas.
    """)

    relatorio_oficial_path = os.path.join(
        ROOT_DIR, "outputs", "relatorios", f"relatorio_oficial_{municipio_sel.lower()}.pdf"
    )
    if not os.path.exists(relatorio_oficial_path):
        relatorio_oficial_path = os.path.join(
            ROOT_DIR, "outputs", "relatorios", "relatorio_oficial_obidos.pdf"
        )

    if os.path.exists(relatorio_oficial_path):
        with open(relatorio_oficial_path, "rb") as f_pdf:
            pdf_data = f_pdf.read()

        st.success(
            f"Relatório Técnico Oficial compilado e disponível para download ({len(pdf_data) / 1024 / 1024:.2f} MB)."
        )
        st.download_button(
            label=f"Download do Relatório Oficial ({municipio_sel}.pdf)",
            data=pdf_data,
            file_name=f"relatorio_tecnico_queimadas_{municipio_sel.lower()}_{ano_sel}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
    else:
        st.info(
            "O relatório oficial ainda não foi compilado. Execute o pipeline de dados para gerá-lo."
        )


# ==============================================================================
# RODAPÉ OFICIAL
# ==============================================================================
st.markdown("---")
st.html("""
<div style="text-align: center; color: #64748b; font-size: 0.85rem; padding: 1.5rem 0;">
    <p style="margin: 0;"><b>Projeto Queimadas Pro</b> — Plataforma de Inteligência e Monitoramento Geoespacial</p>
    <p style="margin: 4px 0 0 0;">Dados públicos abertos fornecidos pelo <b>INPE / BDQueimadas</b> | Desenvolvido com Streamlit, Plotly & ReportLab</p>
</div>
""")
