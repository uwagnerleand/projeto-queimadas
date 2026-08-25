import io
import os
import zipfile
from datetime import datetime
from io import BytesIO

import altair as alt
import folium
import pandas as pd
import requests
import streamlit as st
from streamlit_folium import st_folium

# =========================
# 📦 IMPORTS PARA EXPORTAÇÃO GEOESPACIAL (OPCIONAIS)
# =========================
# NOTA: Caso não esteja disponível, as funcionalidades geoespaciais
# serão desabilitadas. Para instalar: conda install geopandas
try:
    import geopandas as gpd
    from shapely.geometry import Point
    GEOESPACIAL_DISPONIVEL = True
except (ImportError, OSError):
    gpd = None
    Point = None
    GEOESPACIAL_DISPONIVEL = False
import tempfile

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
DATA_FILE = os.path.join(ROOT_DIR, "dados", "tratado", "queimadas_tratado.csv")
LOGO_FILE = os.path.join(ROOT_DIR, "assets", "logo_q.png")
ICON_FILE = os.path.join(ROOT_DIR, "assets", "icon.png")
INPE_YEARS = [2020, 2021, 2022, 2024]

# =========================
# 🎨 CONFIG + TEMA PREMIUM
# =========================
st.set_page_config(
    page_title="Projeto Queimadas - Monitoramento",
    page_icon=ICON_FILE if os.path.exists(ICON_FILE) else "🔥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================
# 🎨 CSS PREMIUM - IHC MELHORADA
# =========================
st.markdown("""
<style>

/* =========================================
   VARIÁVEIS GLOBAIS
========================================= */
:root {
    --primary-color: #2563eb;
    --primary-hover: #1d4ed8;
    --primary-active: #1e40af;

    --secondary-color: #16a34a;
    --secondary-hover: #15803d;

    --danger-color: #dc2626;
    --warning-color: #f59e0b;

    --bg-main: #f8fafc;
    --bg-card: #ffffff;
    --bg-sidebar: #0f172a;

    --text-primary: #1e293b;
    --text-secondary: #64748b;
    --text-light: #94a3b8;

    --border-color: #e2e8f0;

    --shadow-sm: 0 1px 2px rgba(0,0,0,0.05);
    --shadow-md: 0 4px 6px rgba(0,0,0,0.08);
    --shadow-lg: 0 10px 20px rgba(0,0,0,0.10);

    --radius-sm: 8px;
    --radius-md: 12px;
    --radius-lg: 16px;
}

/* =========================================
   APP
========================================= */

.stApp {
    background-color: var(--bg-main);
}

/* =========================================
   TIPOGRAFIA
========================================= */

h1, h2, h3, h4, h5, h6 {
    color: var(--text-primary) !important;
    font-weight: 700 !important;
    letter-spacing: -0.02em;
}

p, span, label {
    color: var(--text-primary);
}

/* =========================================
   SIDEBAR
========================================= */

section[data-testid="stSidebar"] {
    background: linear-gradient(
        180deg,
        #0f172a 0%,
        #1e293b 100%
    );

    border-right: 1px solid rgba(255,255,255,0.08);
}

/* TEXTO SOMENTE DA SIDEBAR */

section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3,
section[data-testid="stSidebar"] h4,
section[data-testid="stSidebar"] h5,
section[data-testid="stSidebar"] h6 {
    color: #F9FAFB !important;
}

section[data-testid="stSidebar"] hr {
    border-color: rgba(255,255,255,0.08) !important;
}

/* =========================================
   SELECTBOX STREAMLIT
========================================= */

div[data-baseweb="select"] > div {
    background-color: #111827 !important;

    border: 1px solid #4B5563 !important;

    border-radius: 10px !important;

    min-height: 46px !important;

    transition: all 0.2s ease !important;
}

/* Hover */

div[data-baseweb="select"] > div:hover {
    border-color: #6B7280 !important;
}

/* Focus */

div[data-baseweb="select"]:focus-within > div {
    border-color: #3B82F6 !important;

    box-shadow: 0 0 0 3px rgba(59,130,246,0.25) !important;
}

/* Texto */

div[data-baseweb="select"] span {
    color: #F9FAFB !important;

    font-weight: 500 !important;
}

/* Input */

div[data-baseweb="select"] input {
    color: #F9FAFB !important;
}

/* Placeholder */

div[data-baseweb="select"] input::placeholder {
    color: #9CA3AF !important;
}

/* Ícone */

div[data-baseweb="select"] svg {
    color: #D1D5DB !important;
}

/* =========================================
   DROPDOWN ABERTO
========================================= */

div[role="listbox"] {
    background-color: #111827 !important;

    border: 1px solid #4B5563 !important;

    border-radius: 10px !important;

    overflow: hidden !important;

    box-shadow: 0 10px 30px rgba(0,0,0,0.35) !important;
}

/* Opções */

div[role="option"] {
    background-color: #111827 !important;

    color: #F9FAFB !important;

    padding: 10px 14px !important;

    transition: all 0.15s ease !important;
}

/* Hover */

div[role="option"]:hover {
    background-color: #374151 !important;

    color: #FFFFFF !important;
}

/* Selecionado */

div[role="option"][aria-selected="true"] {
    background-color: #1F2937 !important;

    color: #FFFFFF !important;

    font-weight: 600 !important;

    border-left: 3px solid #3B82F6 !important;
}

/* =========================================
   SCROLLBAR
========================================= */

div[role="listbox"]::-webkit-scrollbar {
    width: 8px;
}

div[role="listbox"]::-webkit-scrollbar-track {
    background: #111827;
}

div[role="listbox"]::-webkit-scrollbar-thumb {
    background: #4B5563;

    border-radius: 999px;
}

div[role="listbox"]::-webkit-scrollbar-thumb:hover {
    background: #6B7280;
}

/* =========================================
   BOTÕES
========================================= */

/* BOTÃO NORMAL */

.stButton > button {

    background: linear-gradient(
        135deg,
        #2563eb 0%,
        #7c3aed 100%
    ) !important;

    color: white !important;

    border: none !important;

    border-radius: 10px !important;

    font-weight: 700 !important;

    padding: 0.65rem 1rem !important;

    transition: all 0.2s ease !important;

    box-shadow: 0 4px 12px rgba(37, 99, 235, 0.25) !important;
}

/* DOWNLOAD BUTTON */

.stDownloadButton > button {

    background: linear-gradient(
        135deg,
        #16a34a 0%,
        #15803d 100%
    ) !important;

    color: #ffffff !important;

    border: none !important;

    border-radius: 10px !important;

    font-weight: 700 !important;

    padding: 0.65rem 1rem !important;

    transition: all 0.2s ease !important;

    box-shadow: 0 4px 12px rgba(22, 163, 74, 0.25) !important;
}

.stDownloadButton > button:active {

    transform: scale(0.98);

    background: #166534 !important;
}

/* Garantir texto branco e ícones visíveis nos botões de download */
.stDownloadButton > button span {
    color: #ffffff !important;
}

.stDownloadButton > button svg {
    fill: #ffffff !important;
    stroke: #ffffff !important;
    color: #ffffff !important;
}

.stDownloadButton > button:hover span {
    color: #ffffff !important;
}

.stDownloadButton > button:active span {
    color: #ffffff !important;
}

/* Aplicar texto branco diretamente no botão de download */
.stDownloadButton button {
    color: #ffffff !important;
}

.stDownloadButton button span {
    color: #ffffff !important;
}

.stDownloadButton button p,
.stDownloadButton button p span {
    color: #ffffff !important;
}

/* =========================================
   BOTÃO NORMAL - Garantir texto branco
========================================= */

.stButton > button span {
    color: #ffffff !important;
}

.stButton > button svg {
    fill: #ffffff !important;
    stroke: #ffffff !important;
    color: #ffffff !important;
}

.stButton > button:hover span {
    color: #ffffff !important;
}

.stButton > button:active span {
    color: #ffffff !important;
}

/* Aplicar texto branco diretamente no botão normal */
.stButton button {
    color: #ffffff !important;
}

.stButton button span {
    color: #ffffff !important;
}

.stButton button p,
.stButton button p span {
    color: #ffffff !important;
}

/* Estados de foco e acessibilidade para botões */
.stDownloadButton > button:focus {
    outline: 3px solid #fbbf24 !important;
    outline-offset: 2px !important;
}

.stButton > button:focus {
    outline: 3px solid #fbbf24 !important;
    outline-offset: 2px !important;
}

/* Melhorar contraste e brilho no hover dos botões de download */
.stDownloadButton > button:hover {
    background: linear-gradient(
        135deg,
        #22c55e 0%,
        #16a34a 100%
    ) !important;
    color: white !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 8px 20px rgba(34, 197, 94, 0.4) !important;
}

/* Melhorar contraste e brilho no hover dos botões normais */
.stButton > button:hover {
    background: linear-gradient(
        135deg,
        #3b82f6 0%,
        #8b5cf6 100%
    ) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 8px 20px rgba(59, 130, 246, 0.4) !important;
}

/* =========================================
   CARDS
========================================= */

.content-card,
.metric-card {

    background: var(--bg-card);

    border-radius: var(--radius-md);

    border: 1px solid var(--border-color);

    padding: 1.5rem;

    box-shadow: var(--shadow-sm);

    color: var(--text-primary) !important;
}

.metric-card:hover {

    transform: translateY(-2px);

    box-shadow: var(--shadow-lg);
}

/* =========================================
   HEADER
========================================= */

.header-container {

    background: linear-gradient(
        135deg,
        var(--primary-color) 0%,
        #7c3aed 100%
    );

    border-radius: var(--radius-lg);

    padding: 2rem;

    color: white;

    box-shadow: var(--shadow-lg);
}

.header-title {
    color: white !important;
}

.header-subtitle {
    color: rgba(255,255,255,0.9) !important;
}

/* =========================================
   TABS
========================================= */

.stTabs [data-baseweb="tab-list"] {

    background: white;

    border-radius: var(--radius-md);

    padding: 0.25rem;

    border: 1px solid var(--border-color);
}

.stTabs [data-baseweb="tab"] {

    border-radius: var(--radius-sm);

    transition: 0.2s ease;

    color: var(--text-primary) !important;
}

.stTabs [aria-selected="true"] {

    background: linear-gradient(
        135deg,
        var(--primary-color) 0%,
        #7c3aed 100%
    ) !important;

    color: white !important;
}

/* =========================================
   DATAFRAME
========================================= */

.stDataFrame {

    border-radius: var(--radius-md);

    overflow: hidden;
}

/* =========================================
   EXPANDER
========================================= */

.streamlit-expanderHeader {

    border-radius: var(--radius-sm);

    border: 1px solid var(--border-color);

    background: #f8fafc !important;

    color: var(--text-primary) !important;
}

/* =========================================
   TEXTO DO CONTEÚDO PRINCIPAL
========================================= */

.main .block-container,
.main .block-container p,
.main .block-container span,
.main .block-container div,
.main .block-container label {
    color: #1e293b !important;
}

/* Métricas */

.metric-label {
    color: #64748b !important;
}

.metric-value {
    color: #1e293b !important;
}

.metric-trend {
    color: #64748b !important;
}

/* =========================================
   RESPONSIVIDADE
========================================= */

@media (max-width: 768px) {

    .header-container {
        padding: 1.5rem;
    }

    .header-title {
        font-size: 1.5rem !important;
    }
}

</style>
""", unsafe_allow_html=True)

# =========================
# �️ FUNÇÕES DE EXPORTAÇÃO GEOESPACIAL
# =========================

def preparar_exportacao(df):
    """
    Normaliza colunas de exportação convertendo datetimes para string.
    Preserva a coluna geometry se for um GeoDataFrame.
    """
    if GEOESPACIAL_DISPONIVEL and isinstance(df, gpd.GeoDataFrame):
        df_export = df.copy()
    else:
        df_export = df.copy()

    # Evitar processamento da coluna geometry
    geometry_col = None
    if GEOESPACIAL_DISPONIVEL and isinstance(df_export, gpd.GeoDataFrame):
        geometry_col = df_export.geometry.name

    datetime_cols = [
        col for col in df_export.columns
        if col != geometry_col and df_export[col].dtype in ['datetime64[ns]', 'datetime64[ns, UTC]']
    ]
    for col in datetime_cols:
        df_export[col] = df_export[col].dt.strftime('%Y-%m-%d %H:%M:%S')

    object_cols = [
        col for col in df_export.columns
        if col != geometry_col and (
            pd.api.types.is_object_dtype(df_export[col]) or
            pd.api.types.is_string_dtype(df_export[col])
        )
    ]
    for col in object_cols:
        df_export[col] = df_export[col].apply(
            lambda x: x.isoformat() if isinstance(x, (pd.Timestamp, datetime)) else x
        )

    return df_export


def criar_geodataframe(df):
    """
    Cria um GeoDataFrame a partir de um DataFrame com latitude e longitude.
    Requer geopandas e shapely instalados.
    """
    if not GEOESPACIAL_DISPONIVEL:
        raise ValueError(
            "Pacotes geoespaciais não disponíveis. "
            "Instale com: conda install geopandas"
        )

    df_geo = preparar_exportacao(df)

    # Verificar se as colunas existem
    if 'latitude' not in df_geo.columns or 'longitude' not in df_geo.columns:
        raise ValueError("Colunas 'latitude' e 'longitude' são obrigatórias.")

    # Converter para numérico e remover NaN
    df_geo = df_geo.copy()
    df_geo['latitude'] = pd.to_numeric(df_geo['latitude'], errors='coerce')
    df_geo['longitude'] = pd.to_numeric(df_geo['longitude'], errors='coerce')
    df_geo = df_geo.dropna(subset=['latitude', 'longitude'])

    if df_geo.empty:
        raise ValueError("Nenhum dado válido encontrado após conversão para numérico.")

    # Filtrar coordenadas válidas (latitude -90 a 90, longitude -180 a 180)
    df_geo = df_geo[
        (df_geo['latitude'].between(-90, 90)) &
        (df_geo['longitude'].between(-180, 180))
    ]

    if df_geo.empty:
        raise ValueError("Nenhuma coordenada válida encontrada após validação de limites.")

    # Criar geometrias
    geometry = [Point(lon, lat) for lon, lat in zip(df_geo.longitude, df_geo.latitude)]

    # Criar GeoDataFrame
    gdf = gpd.GeoDataFrame(df_geo, geometry=geometry, crs="EPSG:4326")

    # Validar geometrias
    gdf = gdf[gdf.geometry.notna()]

    if gdf.empty:
        raise ValueError("Nenhuma geometria válida criada.")

    return gdf


def exportar_shapefile_zip(gdf):
    """
    Exporta GeoDataFrame para Shapefile compactado em ZIP.
    Retorna bytes do arquivo ZIP.
    """
    if gdf.empty or gdf.geometry.is_empty.all():
        return None

    gdf_export = preparar_exportacao(gdf)

    with tempfile.TemporaryDirectory() as temp_dir:
        # IMPORTANTE: adicionar .shp ao caminho para que GeoPandas crie arquivos, não diretório
        shp_path = os.path.join(temp_dir, "queimadas.shp")

        try:
            gdf_export.to_file(shp_path, driver="ESRI Shapefile", encoding="utf-8")

            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                # Adicionar todos os arquivos .shp* do diretório
                for filename in os.listdir(temp_dir):
                    file_path = os.path.join(temp_dir, filename)
                    if os.path.isfile(file_path):
                        zip_file.write(file_path, filename)

            zip_buffer.seek(0)
            return zip_buffer.getvalue()

        except Exception:
            return None


def exportar_geojson(gdf):
    """
    Exporta GeoDataFrame para GeoJSON.
    Retorna bytes do GeoJSON.
    """
    try:
        gdf_export = preparar_exportacao(gdf)
        geojson_str = gdf_export.to_json(indent=2)
        return geojson_str.encode('utf-8')
    except Exception as e:
        st.error(f"Erro ao exportar GeoJSON: {str(e)}")
        return None


def exportar_csv(df):
    """
    Exporta DataFrame para CSV.
    Retorna bytes do CSV.
    """
    try:
        df_export = preparar_exportacao(df)
        csv_buffer = BytesIO()
        df_export.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
        csv_buffer.seek(0)
        return csv_buffer.getvalue()
    except Exception as e:
        st.error(f"Erro ao exportar CSV: {str(e)}")
        return None

# =========================
# �📥 DADOS
# =========================

def carregar_dados_inpe_ano(ano):
    url = f"https://dataserver-coids.inpe.br/queimadas/queimadas/focos/csv/anual/Brasil_sat_ref/focos_br_ref_{ano}.zip"
    response = requests.get(url, timeout=60)
    response.raise_for_status()

    zip_file = zipfile.ZipFile(io.BytesIO(response.content))
    arquivos = zip_file.namelist()
    nome_csv = next((f for f in arquivos if f.endswith(".csv")), None)
    if nome_csv is None:
        raise FileNotFoundError(f"Nenhum arquivo CSV encontrado no ZIP do INPE para o ano {ano}.")

    try:
        with zip_file.open(nome_csv) as f:
            df = pd.read_csv(f)
    except Exception:
        with zip_file.open(nome_csv) as f:
            df = pd.read_csv(f, encoding="latin1")

    df.columns = df.columns.str.lower()
    if "estado" in df.columns:
        df["estado"] = df["estado"].astype(str).str.upper()
    if "municipio" in df.columns:
        df["municipio"] = df["municipio"].astype(str).str.upper()

    if "datahora" in df.columns:
        col_data = "datahora"
    elif "data" in df.columns:
        col_data = "data"
    elif "data_pas" in df.columns:
        col_data = "data_pas"
    else:
        raise FileNotFoundError(f"Coluna de data não encontrada no CSV do INPE para o ano {ano}.")

    df["data"] = pd.to_datetime(df[col_data], errors="coerce")
    df = df.dropna(subset=["data"])

    df["mes"] = df["data"].dt.month
    df["ano"] = df["data"].dt.year

    return df


def carregar_dados_inpe():
    dfs = []
    for ano in INPE_YEARS:
        dfs.append(carregar_dados_inpe_ano(ano))

    df = pd.concat(dfs, ignore_index=True)
    df = df.drop_duplicates()
    return df


@st.cache_data
def carregar_dados():
    df = None
    if os.path.exists(DATA_FILE):
        try:
            df_temp = pd.read_csv(DATA_FILE, low_memory=False)
            if "data" in df_temp.columns and len(df_temp) > 10:
                df = df_temp
        except Exception:
            df = None

    if df is None:
        df = carregar_dados_inpe()

    df = df.rename(columns={"lat": "latitude", "lon": "longitude", "long": "longitude"})

    df["data"] = pd.to_datetime(df["data"], errors="coerce")
    df = df.dropna(subset=["data"])

    df["mes"] = df["data"].dt.month
    df["ano"] = df["data"].dt.year

    df["municipio"] = df["municipio"].astype(str).str.upper().str.strip()
    df["estado"] = df["estado"].astype(str).str.upper().str.strip()

    return df


try:
    df = carregar_dados()
except Exception as exc:
    st.error("Não foi possível carregar os dados de queimadas.")
    st.write(f"Caminho verificado: {DATA_FILE}")
    st.exception(exc)
    st.stop()

# =========================
# 🎛️ SIDEBAR - FILTROS
# =========================
with st.sidebar:
    # Logo na sidebar
    if os.path.exists(LOGO_FILE):
        st.image(LOGO_FILE, width=80)

    st.title("⚙️ Filtros")
    st.markdown("---")

    # Botão de limpar cache
    if st.button("🔄 Limpar Cache", width="stretch"):
        st.cache_data.clear()
        st.rerun()

    st.markdown("---")

    # Filtros
    estado_sel = st.selectbox(
        "📍 Estado",
        sorted(df["estado"].unique()),
        help="Selecione o estado para filtrar os dados"
    )

    df_estado = df[df["estado"] == estado_sel]

    municipio_sel = st.selectbox(
        "🏙️ Município",
        sorted(df_estado["municipio"].unique()),
        help="Selecione o município para análise detalhada"
    )

    ano_sel = st.selectbox(
        "📅 Ano",
        sorted(df["ano"].unique(), reverse=True),
        help="Selecione o ano de referência"
    )

    # Informações adicionais
    st.markdown("---")
    st.markdown("### 📊 Resumo")
    df_filtrado = df[
        (df["estado"] == estado_sel) &
        (df["municipio"] == municipio_sel) &
        (df["ano"] == ano_sel)
    ]
    df_estado_ano = df[
        (df["estado"] == estado_sel) &
        (df["ano"] == ano_sel)
    ]

    st.metric("Total de focos", len(df_filtrado))
    st.metric("Focos no estado", len(df_estado_ano))

    # Debug expander
    with st.expander("🔍 Informações Técnicas"):
        st.write(f"**Anos disponíveis:** {sorted(df['ano'].unique(), reverse=True)}")
        st.write(f"**Total de registros:** {len(df):,}")
        st.write(f"**Última atualização:** {datetime.now().strftime('%d/%m/%Y %H:%M')}")

# =========================
# 🧠 HEADER PRINCIPAL
# =========================
col_logo, col_title = st.columns([1, 5])

with col_logo:
    if os.path.exists(LOGO_FILE):
        st.image(LOGO_FILE, width=80)
    else:
        st.markdown("🔥", unsafe_allow_html=True)

with col_title:
    st.markdown(f"""
    <div style="padding-top: 0.5rem;">
        <h1 style="color: var(--text-primary); font-size: 2rem; font-weight: 700; margin-bottom: 0.25rem;">Monitoramento de Queimadas</h1>
        <p style="color: var(--text-secondary); font-size: 1rem; margin: 0;">{municipio_sel} - {estado_sel} | Ano: {ano_sel}</p>
    </div>
    """, unsafe_allow_html=True)

# =========================
# 📊 MÉTRICAS PRINCIPAIS
# =========================
col1, col2, col3 = st.columns(3, gap="large")

total_focos = len(df_filtrado)
media_mensal = df_filtrado.groupby("mes").size().mean() if not df_filtrado.empty else 0
total_estado = len(df_estado_ano)
percentual = (total_focos / total_estado * 100) if total_estado > 0 else 0

with col1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-icon">🔥</div>
        <div class="metric-label">Total de Focos</div>
        <div class="metric-value">{total_focos:,}</div>
        <div class="metric-trend">No município selecionado</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-icon">📊</div>
        <div class="metric-label">Média Mensal</div>
        <div class="metric-value">{media_mensal:,.1f}</div>
        <div class="metric-trend">Focos por mês (média)</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-icon">📍</div>
        <div class="metric-label">% no Estado</div>
        <div class="metric-value">{percentual:.2f}%</div>
        <div class="metric-trend">Representatividade no estado</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# =========================
# 📑 ABAS DE CONTEÚDO
# =========================
tab1, tab2, tab3, tab4 = st.tabs([
    "📈 Análise Temporal",
    "🗺️ Mapa de Calor",
    "🏆 Ranking Municipal",
    "📋 Dados Completos"
])

# =========================
# 📈 ANÁLISE TEMPORAL
# =========================
with tab1:
    # Gráfico de Distribuição Mensal
    st.markdown("""
    <div class="content-card">
        <div class="content-card-title">
            <span>📊</span> Distribuição Mensal de Focos
        </div>
    </div>
    """, unsafe_allow_html=True)

    if not df_filtrado.empty:
        grafico = df_filtrado.groupby("mes").size().reset_index(name="focos")

        meses = {
            1:"Jan", 2:"Fev", 3:"Mar", 4:"Abr", 5:"Mai", 6:"Jun",
            7:"Jul", 8:"Ago", 9:"Set", 10:"Out", 11:"Nov", 12:"Dez"
        }

        meses_completos = pd.DataFrame({"mes": list(range(1, 13))})
        grafico = meses_completos.merge(grafico, on="mes", how="left").fillna({"focos": 0})
        grafico["mes_nome"] = grafico["mes"].map(meses)

        # Cores baseadas na intensidade
        max_focos = grafico["focos"].max()
        if max_focos == 0:
            grafico["cor"] = "rgb(37, 99, 235)"
        else:
            grafico["cor"] = grafico["focos"].apply(
                lambda x: f"rgb({int(37 + (x/max_focos)*183)}, {int(99 + (x/max_focos)*66)}, {int(235 + (x/max_focos)*10)})"
            )

        chart = alt.Chart(grafico).mark_bar(
            cornerRadius=8,
            opacity=0.9
        ).encode(
            x=alt.X("mes_nome:N",
                    title="Mês",
                    sort=list(meses.values()),
                    axis=alt.Axis(labelFontSize=12, titleFontSize=14, labelFontWeight=600, labelColor="#374151", titleColor="#1f2937")),
            y=alt.Y("focos:Q",
                    title="Número de Focos",
                    axis=alt.Axis(labelFontSize=12, titleFontSize=14, labelFontWeight=600, labelColor="#374151", titleColor="#1f2937")),
            color=alt.Color("cor:N", scale=None),
            tooltip=[
                alt.Tooltip("mes_nome:N", title="Mês"),
                alt.Tooltip("focos:Q", title="Focos", format=",")
            ]
        ).properties(
            height=350,
            background="#ffffff"
        ).configure_view(
            strokeWidth=0
        ).configure_axis(
            grid=True,
            gridColor="#f1f5f9",
            labelColor="#374151",
            titleColor="#1f2937"
        )

        st.altair_chart(chart, width="stretch")
    else:
        st.warning("⚠️ Sem dados disponíveis para o período selecionado.")

    st.markdown("<br>", unsafe_allow_html=True)

    # Gráfico de Evolução Histórica
    st.markdown("""
    <div class="content-card">
        <div class="content-card-title">
            <span>📈</span> Evolução Histórica
        </div>
    </div>
    """, unsafe_allow_html=True)

    modo_historico = st.radio(
        "Escopo temporal:",
        ["Série Histórica Completa (Todos os Anos)", f"Apenas o Ano Selecionado ({ano_sel})"],
        horizontal=True
    )

    if modo_historico.startswith("Série Histórica"):
        df_evolucao = df[(df["estado"] == estado_sel) & (df["municipio"] == municipio_sel)].copy()
    else:
        df_evolucao = df_filtrado.copy()

    serie = df_evolucao.groupby(["ano", "mes"]).size().reset_index(name="focos")

    if not serie.empty:
        serie["data"] = pd.to_datetime(
            serie["ano"].astype(str) + "-" + serie["mes"].astype(str).str.zfill(2) + "-01"
        )
        serie = serie.sort_values("data")

        chart = alt.Chart(serie).mark_line(
            color="#2563eb",
            point=alt.OverlayMarkDef(color="#2563eb", filled=True, size=60),
            strokeWidth=3
        ).encode(
            x=alt.X("data:T",
                    title="Período",
                    axis=alt.Axis(format="%b %Y", labelFontSize=12, titleFontSize=14, labelColor="#374151", titleColor="#1f2937")),
            y=alt.Y("focos:Q",
                    title="Focos",
                    axis=alt.Axis(labelFontSize=12, titleFontSize=14, labelColor="#374151", titleColor="#1f2937")),
            tooltip=[
                alt.Tooltip("data:T", title="Data", format="%b %Y"),
                alt.Tooltip("focos:Q", title="Focos", format=",")
            ]
        ).properties(
            height=350,
            background="#ffffff"
        ).configure_view(
            strokeWidth=0
        ).configure_axis(
            grid=True,
            gridColor="#f1f5f9",
            labelColor="#374151",
            titleColor="#1f2937"
        )

        st.altair_chart(chart, width="stretch")
    else:
        st.warning("⚠️ Sem dados históricos disponíveis.")

# =========================
# 🗺️ MAPA DE CALOR
# =========================
with tab2:
    st.markdown("""
    <div class="content-card">
        <div class="content-card-title">
            <span>🗺️</span> Mapa de Localização dos Focos
        </div>
    </div>
    """, unsafe_allow_html=True)

    df_mapa = df_filtrado.dropna(subset=["latitude", "longitude"])

    if not df_mapa.empty:
        # Criar mapa com estilo mais moderno
        m = folium.Map(
            location=[df_mapa["latitude"].mean(), df_mapa["longitude"].mean()],
            zoom_start=8,
            tiles="CartoDB positron"  # Estilo mais limpo
        )

        # Adicionar marcador para o centro
        folium.Marker(
            location=[df_mapa["latitude"].mean(), df_mapa["longitude"].mean()],
            popup=f"Centro: {municipio_sel} - {estado_sel}",
            icon=folium.Icon(color="blue", icon="map-marker", prefix="fa")
        ).add_to(m)

        # Adicionar círculos para cada foco
        for _, row in df_mapa.iterrows():
            folium.CircleMarker(
                location=[row["latitude"], row["longitude"]],
                radius=5,
                color="#dc2626",
                fillColor="#dc2626",
                fill=True,
                fill_opacity=0.6,
                weight=2,
                popup=f"Foco detectado<br>Lat: {row['latitude']:.4f}<br>Lon: {row['longitude']:.4f}"
            ).add_to(m)

        st_folium(m, width="100%", height=550)
    else:
        st.warning("⚠️ Sem coordenadas geográficas disponíveis para exibição no mapa.")

# =========================
# 🏆 RANKING MUNICIPAL
# =========================
with tab3:
    st.markdown("""
    <div class="content-card">
        <div class="content-card-title">
            <span>🏆</span> Top 10 Municípios com Mais Focos
        </div>
        <p style="color: var(--text-secondary); margin-bottom: 1rem;">Ranking dos municípios do estado {estado_sel} no ano {ano_sel}</p>
    </div>
    """.format(estado_sel=estado_sel, ano_sel=ano_sel), unsafe_allow_html=True)

    ranking = df_estado_ano.groupby("municipio").size().reset_index(name="focos")
    top10 = ranking.sort_values("focos", ascending=False).head(10)

    if not top10.empty:
        # Adicionar posição
        top10["posicao"] = range(1, len(top10) + 1)
        top10["municipio_label"] = top10.apply(
            lambda row: f"{int(row['posicao'])}º - {row['municipio']}", axis=1
        )

        # Cores baseadas na posição
        def get_color(pos: int) -> str:
            if pos == 1:
                return "#fbbf24"  # Ouro
            if pos == 2:
                return "#94a3b8"  # Prata
            if pos == 3:
                return "#b45309"  # Bronze
            return "#2563eb"  # Azul

        top10["cor"] = top10["posicao"].apply(get_color)

        chart = alt.Chart(top10).mark_bar(
            cornerRadius=8,
            opacity=0.9
        ).encode(
            x=alt.X("focos:Q",
                    title="Número de Focos",
                    axis=alt.Axis(labelFontSize=12, titleFontSize=14, labelColor="#374151", titleColor="#1f2937")),
            y=alt.Y("municipio_label:N",
                    sort="-x",
                    title="",
                    axis=alt.Axis(labelFontSize=11, labelFontWeight=600, labelColor="#374151")),
            color=alt.Color("cor:N", scale=None, legend=None),
            tooltip=[
                alt.Tooltip("posicao:Q", title="Posição", format=".0f"),
                alt.Tooltip("municipio:N", title="Município"),
                alt.Tooltip("focos:Q", title="Focos", format=",")
            ]
        ).properties(
            height=400,
            background="#ffffff"
        ).configure_view(
            strokeWidth=0
        ).configure_axis(
            grid=True,
            gridColor="#f1f5f9",
            labelColor="#374151",
            titleColor="#1f2937"
        )

        st.altair_chart(chart, width="stretch")

        # Posição do município selecionado
        if municipio_sel in ranking["municipio"].values:
            pos = ranking.sort_values("focos", ascending=False)\
                         .reset_index()\
                         .query("municipio == @municipio_sel")\
                         .index[0] + 1

            emoji = "🥇" if pos == 1 else "🥈" if pos == 2 else "🥉" if pos == 3 else "📍"

            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
                        border-radius: 12px; padding: 1rem 1.5rem; margin-top: 1rem;
                        border: 1px solid #bae6fd; display: inline-block;">
                <span style="font-size: 1.25rem; font-weight: 600; color: #0369a1;">
                    {emoji} {municipio_sel} está na posição #{pos} no ranking estadual
                </span>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.warning("⚠️ Sem dados para gerar o ranking.")

# =========================
# 📋 DADOS COMPLETOS
# =========================
with tab4:

    # =========================
    # 📋 HEADER
    # =========================
    st.markdown("""
    <div class="content-card">
        <div class="content-card-title">
            <span>📋</span> Base de Dados Completa
        </div> <p style=" color: var(--text-secondary); margin-top: 0.5rem; margin-bottom: 0; line-height: 1.6; "> Visualize, filtre e exporte os registros de queimadas do município selecionado em formatos tabulares e geoespaciais. </p> </div>
    """, unsafe_allow_html=True)

    # =========================
    # 📊 INFO RÁPIDA
    # =========================
    st.info(
        f"📊 {len(df_filtrado):,} registros encontrados | "
        f"🕒 Atualizado em {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    )

    # =========================
    # 📄 DATAFRAME
    # =========================
    st.dataframe(
        df_filtrado,
        width="stretch",
        height=450,
        hide_index=True
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # =========================
    # 📥 EXPORTAÇÃO
    # =========================
    st.markdown("""
    <div style="
        background: white;
        padding: 1.5rem;
        border-radius: 16px;
        border: 1px solid #e2e8f0;
        margin-bottom: 1.5rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    "> <h3 style="color:#0f172a;margin-bottom:0.4rem;">📥 Exportação de Dados</h3> <p style=" color:#64748b; margin:0; line-height:1.5;"> Baixe os dados filtrados em formatos compatíveis com planilhas, sistemas GIS e plataformas web. </p> </div>
    """, unsafe_allow_html=True)

    # =========================
    # 📦 GEO DATAFRAME
    # =========================
    if GEOESPACIAL_DISPONIVEL:
        try:
            gdf = criar_geodataframe(df_filtrado)
        except Exception as e:
            gdf = None
            st.warning(f"⚠️ Exportação SIG indisponível: {str(e)}")
    else:
        gdf = None

    # =========================
    # 🎛️ BOTÕES
    # =========================
    col1, col2 = st.columns(2)

    # =========================
    # 📄 FORMATOS TABULARES
    # =========================
    with col1:

        st.markdown("### 📄 Formatos Tabulares")

        # CSV
        csv_data = exportar_csv(df_filtrado)

        st.download_button(
            label="⬇️ Baixar CSV",
            data=csv_data,
            file_name=f"queimadas_{municipio_sel}_{ano_sel}.csv",
            mime="text/csv",
            width="stretch",
            help="Compatível com Excel e LibreOffice"
        )

        # EXCEL
        def gerar_excel():

            output = BytesIO()

            with pd.ExcelWriter(
                output,
                engine="openpyxl"
            ) as writer:

                df_filtrado.to_excel(
                    writer,
                    sheet_name="Dados",
                    index=False
                )

                ranking.to_excel(
                    writer,
                    sheet_name="Ranking",
                    index=False
                )

            return output.getvalue()

        excel_data = gerar_excel()

        st.download_button(
            label="⬇️ Baixar Excel",
            data=excel_data,
            file_name=f"queimadas_{municipio_sel}_{ano_sel}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            width="stretch",
            help="Planilha Excel completa"
        )

    # =========================
    # 🗺️ FORMATOS SIG
    # =========================
    with col2:

        st.markdown("### 🗺️ Formatos SIG")

        if not GEOESPACIAL_DISPONIVEL:

            st.info(
                "💡 Exportação para formatos SIG (GeoJSON, Shapefile) requer "
                "geopandas instalado. No Streamlit Cloud, isso não está "
                "disponível por padrão.\n\n"
                "ℹ️ Utilize os formatos tabulares (CSV/Excel) como alternativa."
            )

        elif gdf is not None and not gdf.empty:

            # =====================
            # 🔥 CORRIGE DATETIME
            # =====================
            gdf_export = gdf.copy()

            for col in gdf_export.columns:

                if str(gdf_export[col].dtype).startswith("datetime"):

                    gdf_export[col] = gdf_export[col].astype(str)

            # =====================
            # 🌍 GEOJSON
            # =====================
            try:

                geojson_data = exportar_geojson(gdf_export)

                st.download_button(
                    label="⬇️ Baixar GeoJSON",
                    data=geojson_data,
                    file_name=f"queimadas_{municipio_sel}_{ano_sel}.geojson",
                    mime="application/geo+json",
                    width="stretch",
                    help="Ideal para mapas web e QGIS"
                )

            except Exception as e:

                st.error(f"Erro GeoJSON: {str(e)}")

            # =====================
            # 🗺️ SHAPEFILE
            # =====================
            try:

                shp_zip_data = exportar_shapefile_zip(gdf_export)

                st.download_button(
                    label="⬇️ Baixar Shapefile",
                    data=shp_zip_data,
                    file_name=f"queimadas_{municipio_sel}_{ano_sel}.zip",
                    mime="application/zip",
                    width="stretch",
                    help="Compatível com QGIS e ArcGIS"
                )

            except Exception as e:

                st.error(f"Erro Shapefile: {str(e)}")

        else:

            st.warning(
                "Nenhum dado geoespacial válido encontrado para exportação."
            )
# =========================
# 🦶 FOOTER
# =========================
st.markdown("---")
st.markdown("""
<div style="text-align: center; padding: 1rem; color: var(--text-secondary); font-size: 0.875rem;">
    <p>🔥 <strong>Projeto Queimadas</strong> | Monitoramento de focos de queimadas no Brasil</p>
    <p style="margin-top: 0.25rem;">Dados fornecidos pelo INPE | Desenvolvido com Streamlit</p>
</div>
""", unsafe_allow_html=True)
