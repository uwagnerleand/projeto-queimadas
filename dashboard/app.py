import streamlit as st
import pandas as pd
import folium
import altair as alt
from streamlit_folium import st_folium
from io import BytesIO
import os
import requests
import zipfile
import io
from datetime import datetime

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
    /* === CONFIGURAÇÕES GERAIS === */
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
        --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
        --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
        --radius-sm: 8px;
        --radius-md: 12px;
        --radius-lg: 16px;
    }

    /* Fundo principal */
    .stApp {
        background-color: var(--bg-main);
    }

    /* Tipografia */
    h1, h2, h3, h4, h5, h6 {
        color: var(--text-primary) !important;
        font-weight: 700 !important;
        letter-spacing: -0.025em;
    }

    h1 { font-size: 2.25rem !important; }
    h2 { font-size: 1.75rem !important; }
    h3 { font-size: 1.375rem !important; }
    h4 { font-size: 1.125rem !important; }

    p, span, label, div {
        color: var(--text-primary) !important;
    }

    /* === SIDEBAR PREMIUM === */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }

    section[data-testid="stSidebar"] .stSidebarContent {
        padding-top: 2rem !important;
    }

    section[data-testid="stSidebar"] h1, 
    section[data-testid="stSidebar"] h2, 
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span {
        color: #fFf5f9 !important;
    }

    section[data-testid="stSidebar"] .stSelectbox label {
        color: #ffffff !important;
        font-weight: 600;
    }
    
    /* Melhorar contraste dos selects na sidebar */
    section[data-testid="stSidebar"] .stSelectbox > div > div {
        background-color: #1e293b !important;
        border-color: #475569 !important;
    }
    
    section[data-testid="stSidebar"] .stSelectbox > div > div:hover {
        border-color: #ffffff !important;
    }

    /* === HEADER === */
    .header-container {
        background: linear-gradient(135deg, var(--primary-color) 0%, #7c3aed 100%);
        border-radius: var(--radius-lg);
        padding: 2rem;
        margin-bottom: 1.5rem;
        box-shadow: var(--shadow-xl);
        position: relative;
        overflow: hidden;
    }

    .header-container::before {
        content: '';
        position: absolute;
        top: -50%;
        right: -50%;
        width: 100%;
        height: 200%;
        background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
        pointer-events: none;
    }

    .header-title {
        color: white !important;
        font-size: 2rem !important;
        font-weight: 700 !important;
        margin-bottom: 0.5rem !important;
        position: relative;
        z-index: 1;
    }

    .header-subtitle {
        color: rgba(255, 255, 255, 0.9) !important;
        font-size: 1rem !important;
        font-weight: 400 !important;
        position: relative;
        z-index: 1;
    }

    /* === MÉTRICAS EM CARDS === */
    .metric-card {
        background: var(--bg-card);
        border-radius: var(--radius-md);
        padding: 1.5rem;
        box-shadow: var(--shadow-md);
        border: 1px solid var(--border-color);
        transition: all 0.3s ease;
        height: 100%;
    }

    .metric-card:hover {
        box-shadow: var(--shadow-lg);
        transform: translateY(-2px);
    }

    .metric-icon {
        font-size: 2rem;
        margin-bottom: 0.5rem;
    }

    .metric-label {
        color: var(--text-secondary) !important;
        font-size: 0.875rem !important;
        font-weight: 500 !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.25rem;
    }

    .metric-value {
        color: var(--text-primary) !important;
        font-size: 2rem !important;
        font-weight: 700 !important;
        line-height: 1.2;
    }

    .metric-trend {
        font-size: 0.75rem !important;
        color: var(--text-secondary) !important;
        margin-top: 0.25rem;
    }

    /* === CARDS DE CONTEÚDO === */
    .content-card {
        background: var(--bg-card);
        border-radius: var(--radius-md);
        padding: 1.5rem;
        box-shadow: var(--shadow-md);
        border: 1px solid var(--border-color);
        margin-bottom: 1.5rem;
    }

    .content-card-title {
        color: var(--text-primary) !important;
        font-size: 1.125rem !important;
        font-weight: 600 !important;
        margin-bottom: 1rem !important;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    /* === BOTÕES === */
    div.stButton > button {
        background: linear-gradient(135deg, var(--primary-color) 0%, #7c3aed 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: var(--radius-sm) !important;
        padding: 0.6rem 1.2rem !important;
        font-weight: 600 !important;
        font-size: 0.875rem !important;
        transition: all 0.2s ease !important;
        box-shadow: var(--shadow-sm) !important;
    }

    div.stButton > button:hover {
        background: linear-gradient(135deg, var(--primary-hover) 0%, #6d28d9 100%) !important;
        box-shadow: var(--shadow-md) !important;
        transform: translateY(-1px) !important;
        color: white !important;
    }

    div.stButton > button:active {
        background: linear-gradient(135deg, var(--primary-active) 0%, #5b21b6 100%) !important;
        transform: translateY(0) !important;
    }

    /* Botão Download */
    div.stDownloadButton > button {
        background: linear-gradient(135deg, var(--secondary-color) 0%, #059669 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: var(--radius-sm) !important;
        padding: 0.6rem 1.2rem !important;
        font-weight: 600 !important;
        font-size: 0.875rem !important;
        transition: all 0.2s ease !important;
        box-shadow: var(--shadow-sm) !important;
    }

    div.stDownloadButton > button:hover {
        background: linear-gradient(135deg, var(--secondary-hover) 0%, #047857 100%) !important;
        box-shadow: var(--shadow-md) !important;
        transform: translateY(-1px) !important;
        color: white !important;
    }

    /* === ABAS (TABS) === */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0;
        background: var(--bg-card);
        border-radius: var(--radius-md);
        padding: 0.25rem;
        box-shadow: var(--shadow-sm);
        border: 1px solid var(--border-color);
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: var(--radius-sm);
        padding: 0.75rem 1.25rem;
        font-weight: 500;
        color: var(--text-secondary) !important;
        transition: all 0.2s ease;
        margin: 0 0.125rem;
    }

    .stTabs [data-baseweb="tab"]:hover {
        background-color: #f1f5f9 !important;
        color: var(--text-primary) !important;
    }

    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background: linear-gradient(135deg, var(--primary-color) 0%, #7c3aed 100%) !important;
        color: white !important;
        font-weight: 600;
        box-shadow: var(--shadow-sm);
    }

    /* === SELECTBOX === */
    .stSelectbox > div > div {
        border-radius: var(--radius-sm) !important;
        border: 1px solid var(--border-color) !important;
    }

    .stSelectbox > div > div:hover {
        border-color: var(--primary-color) !important;
    }

    /* === DIVIDER === */
    hr {
        border: none !important;
        border-top: 1px solid var(--border-color) !important;
        margin: 1.5rem 0 !important;
    }

    /* === CONTROLES DO GRÁFICO ALTAIR === */
    .vega-actions button,
    .vega-actions button:hover,
    .vega-actions button:focus {
        background-color: rgba(255,255,255,0.95) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: var(--radius-sm) !important;
        box-shadow: var(--shadow-sm) !important;
    }

    .vega-actions button svg,
    .vega-actions button path {
        fill: var(--text-primary) !important;
        stroke: var(--text-primary) !important;
    }

    /* === EXPANDER === */
    .streamlit-expanderHeader {
        background-color: #f1f5f9 !important;
        border-radius: var(--radius-sm) !important;
        border: 1px solid var(--border-color) !important;
    }

    /* === DATAFRAME === */
    .stDataFrame {
        border-radius: var(--radius-md);
        overflow: hidden;
        box-shadow: var(--shadow-sm);
    }

    /* === STATUS BADGES === */
    .status-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .status-badge-success {
        background-color: #dcfce7;
        color: #166534;
    }

    .status-badge-warning {
        background-color: #fef3c7;
        color: #92400e;
    }

    .status-badge-danger {
        background-color: #fee2e2;
        color: #991b1b;
    }

    /* === ANIMAÇÕES === */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }

    .fade-in {
        animation: fadeIn 0.5s ease-out;
    }

    /* === RESPONSIVIDADE === */
    @media (max-width: 768px) {
        .header-container {
            padding: 1.5rem !important;
        }
        .header-title {
            font-size: 1.5rem !important;
        }
        .metric-value {
            font-size: 1.5rem !important;
        }
    }
</style>
""", unsafe_allow_html=True)

# =========================
# 📥 DADOS
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
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
    else:
        df = carregar_dados_inpe()

    df = df.rename(columns={"lat": "latitude", "lon": "longitude"})

    df["data"] = pd.to_datetime(df["data"], errors="coerce")
    df = df.dropna(subset=["data"])

    df["mes"] = df["data"].dt.month
    df["ano"] = df["data"].dt.year

    df["municipio"] = df["municipio"].astype(str).str.upper().str.strip()
    df["estado"] = df["estado"].astype(str).str.upper().str.strip()

    return df


if not os.path.exists(DATA_FILE):
    st.info(
        "Arquivo local não encontrado nesta implantação. "
        f"O app usará os dados do INPE como fallback para os anos: {', '.join(map(str, INPE_YEARS))}."
    )

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
        
        grafico["mes_nome"] = grafico["mes"].map(meses)
        
        # Cores baseadas na intensidade
        max_focos = grafico["focos"].max()
        grafico["cor"] = grafico["focos"].apply(lambda x: f"rgb({int(37 + (x/max_focos)*183)}, {int(99 + (x/max_focos)*66)}, {int(235 + (x/max_focos)*10)})")
        
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

    df_evolucao = df[
        (df["estado"] == estado_sel) &
        (df["municipio"] == municipio_sel)
    ]

    serie = df_evolucao.groupby(["ano", "mes"]).size().reset_index(name="focos")

    if not serie.empty:
        serie["data"] = pd.to_datetime(
            serie["ano"].astype(str) + "-" + serie["mes"].astype(str) + "-01"
        )

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
        
        # Cores baseadas na posição
        def get_color(pos):
            if pos == 1: return "#fbbf24"  # Ouro
            elif pos == 2: return "#94a3b8"  # Prata
            elif pos == 3: return "#b45309"  # Bronze
            else: return "#2563eb"  # Azul
        
        top10["cor"] = top10["posicao"].apply(get_color)
        
        chart = alt.Chart(top10).mark_bar(
            cornerRadius=8,
            opacity=0.9
        ).encode(
            x=alt.X("focos:Q", 
                    title="Número de Focos",
                    axis=alt.Axis(labelFontSize=12, titleFontSize=14, labelColor="#374151", titleColor="#1f2937")),
            y=alt.Y("municipio:N", 
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
    st.markdown("""
    <div class="content-card">
        <div class="content-card-title">
            <span>📋</span> Base de Dados Completa
        </div>
        <p style="color: var(--text-secondary); margin-bottom: 1rem;">
            Visualize e exporte os dados brutos de queimadas para o município e ano selecionados.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Exibir dataframe com estilização
    st.dataframe(
        df_filtrado,
        width="stretch",
        height=400,
        hide_index=True
    )

    # Botão de download estilizado
    def gerar_excel():
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df_filtrado.to_excel(writer, sheet_name="Dados", index=False)
            ranking.to_excel(writer, sheet_name="Ranking", index=False)
        return output.getvalue()

    col1, col2 = st.columns([1, 4])
    with col1:
        st.download_button(
            label="📥 Baixar Excel",
            data=gerar_excel(),
            file_name=f"queimadas_{municipio_sel}_{ano_sel}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            width="stretch"
        )
    with col2:
        st.caption(f"📊 {len(df_filtrado):,} registros | Última atualização: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

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