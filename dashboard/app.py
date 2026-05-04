import streamlit as st
import pandas as pd
import folium
import altair as alt
from streamlit_folium import st_folium
from io import BytesIO

# =========================
# 🎨 CONFIG + TEMA CORRIGIDO
# =========================
st.set_page_config(
    page_title="Monitoramento de Queimadas",
    layout="wide",
    page_icon="🔥"
)

# CSS corrigido (remove conflito de cor branca)
st.markdown("""
<style>
    .stApp {
        background-color: #f5f7fa;
    }

    /* força textos escuros */
    h1, h2, h3, h4, h5, h6, p, span, label {
        color: #1f2937 !important;
    }

    /* sidebar */
    section[data-testid="stSidebar"] {
        background-color: #111827;
        color: white;
    }

    section[data-testid="stSidebar"] * {
        color: white !important;
    }

    /* métricas */
    div[data-testid="metric-container"] {
        background-color: white;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.05);
    }
                   
    /* Botão Download (principal) */
    div.stDownloadButton > button {
        background-color: #16a34a;   /* cor do fundo */
        color: white;               /* cor do texto */
        border-radius: 10px;
        border: none;
        font-weight: 600;
        padding: 0.6rem 1rem;
    }   

    /* Hover (quando passa o mouse) */
    div.stDownloadButton > button:hover {
        background-color: #2563eb;
        color: white;
    }

    /* Clique */
    div.stDownloadButton > button:active {
        background-color: #166534;
    }
</style>
""", unsafe_allow_html=True)

# =========================
# 📥 DADOS
# =========================
@st.cache_data
def carregar_dados():
    df = pd.read_csv("dados/tratado/queimadas_tratado.csv")

    df = df.rename(columns={"lat": "latitude", "lon": "longitude"})

    df["data"] = pd.to_datetime(df["data"], errors="coerce")
    df = df.dropna(subset=["data"])

    df["mes"] = df["data"].dt.month
    df["ano"] = df["data"].dt.year

    df["municipio"] = df["municipio"].astype(str).str.upper().str.strip()
    df["estado"] = df["estado"].astype(str).str.upper().str.strip()

    return df

df = carregar_dados()

# =========================
# 🎛️ FILTROS
# =========================
st.sidebar.title("🎛️ Filtros")

estado_sel = st.sidebar.selectbox("Estado", sorted(df["estado"].unique()))
df_estado = df[df["estado"] == estado_sel]

municipio_sel = st.sidebar.selectbox("Município", sorted(df_estado["municipio"].unique()))
ano_sel = st.sidebar.selectbox("Ano", sorted(df_estado["ano"].unique()))

df_filtrado = df[
    (df["estado"] == estado_sel) &
    (df["municipio"] == municipio_sel) &
    (df["ano"] == ano_sel)
]

df_estado_ano = df[
    (df["estado"] == estado_sel) &
    (df["ano"] == ano_sel)
]

# =========================
# 🧠 HEADER
# =========================
st.title("🔥 Monitoramento de Queimadas")
st.caption(f"{municipio_sel} - {estado_sel} | Ano: {ano_sel}")

# =========================
# 📊 MÉTRICAS
# =========================
col1, col2, col3 = st.columns(3)

total_focos = len(df_filtrado)
media_mensal = df_filtrado.groupby("mes").size().mean() if not df_filtrado.empty else 0
total_estado = len(df_estado_ano)
percentual = (total_focos / total_estado * 100) if total_estado > 0 else 0

col1.metric("🔥 Total de focos", total_focos)
col2.metric("📊 Média mensal", f"{media_mensal:.1f}")
col3.metric("📍 % no estado", f"{percentual:.2f}%")

st.divider()

# =========================
# 📑 ABAS
# =========================
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Análise",
    "🗺️ Mapa",
    "🏆 Ranking",
    "📄 Dados"
])

# =========================
# 📊 ANÁLISE
# =========================
with tab1:

    st.subheader("Distribuição mensal")

    if not df_filtrado.empty:

        grafico = df_filtrado.groupby("mes").size().reset_index(name="focos")

        meses = {
            1:"Jan",2:"Fev",3:"Mar",4:"Abr",5:"Mai",6:"Jun",
            7:"Jul",8:"Ago",9:"Set",10:"Out",11:"Nov",12:"Dez"
        }

        grafico["mes_nome"] = grafico["mes"].map(meses)

        chart = alt.Chart(grafico).mark_bar(color="#2563eb").encode(
            x=alt.X("mes_nome:N", title="Mês", sort=list(meses.values())),
            y=alt.Y("focos:Q", title="Focos"),
            tooltip=["mes_nome", "focos"]
        ).configure_axis(
            labelColor="#ffffff",
            titleColor="#ffffff"
        )

        st.altair_chart(chart, width="stretch")

    else:
        st.warning("Sem dados")

    # =====================
    st.subheader("Evolução histórica")

    df_evolucao = df[
        (df["estado"] == estado_sel) &
        (df["municipio"] == municipio_sel)
    ]

    serie = df_evolucao.groupby(["ano","mes"]).size().reset_index(name="focos")

    if not serie.empty:

        serie["data"] = pd.to_datetime(
            serie["ano"].astype(str) + "-" + serie["mes"].astype(str)
        )

        chart = alt.Chart(serie).mark_line(color="#dc2626").encode(
            x=alt.X("data:T", title="Tempo"),
            y=alt.Y("focos:Q", title="Focos"),
            tooltip=["data", "focos"]
        ).configure_axis(
            labelColor="#ffffff",
            titleColor="#ffffff"
        )

        st.altair_chart(chart, width="stretch")

    else:
        st.warning("Sem histórico")

# =========================
# 🗺️ MAPA
# =========================
with tab2:

    st.subheader("Mapa de focos")

    df_mapa = df_filtrado.dropna(subset=["latitude", "longitude"])

    if not df_mapa.empty:

        m = folium.Map(
            location=[df_mapa["latitude"].mean(), df_mapa["longitude"].mean()],
            zoom_start=7
        )

        for _, row in df_mapa.iterrows():
            folium.CircleMarker(
                location=[row["latitude"], row["longitude"]],
                radius=4,
                color="#dc2626",
                fill=True,
                fill_opacity=0.7
            ).add_to(m)

        st_folium(m, width=1000, height=500)

    else:
        st.warning("Sem coordenadas")

# =========================
# 🏆 RANKING
# =========================
with tab3:

    ranking = df_estado_ano.groupby("municipio").size().reset_index(name="focos")

    top10 = ranking.sort_values("focos", ascending=False).head(10)

    chart = alt.Chart(top10).mark_bar(color="#16a34a").encode(
        x=alt.X("focos:Q", title="Focos"),
        y=alt.Y("municipio:N", sort="-x"),
        tooltip=["municipio", "focos"]
    ).configure_axis(
        labelColor="#ffffff",
        titleColor="#ffffff"
    )

    st.altair_chart(chart, width="stretch")

    if municipio_sel in ranking["municipio"].values:
        pos = ranking.sort_values("focos", ascending=False)\
                     .reset_index()\
                     .query("municipio == @municipio_sel")\
                     .index[0] + 1
        st.success(f"{municipio_sel} está na posição #{pos}")

# =========================
# 📄 DADOS
# =========================
with tab4:

    st.dataframe(df_filtrado, width="stretch")

    def gerar_excel():
        output = BytesIO()

        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df_filtrado.to_excel(writer, sheet_name="Dados", index=False)
            ranking.to_excel(writer, sheet_name="Ranking")

        return output.getvalue()

    st.download_button(
        "📥 Baixar Excel", 
        data=gerar_excel(),
        file_name=f"queimadas_{municipio_sel}_{ano_sel}.xlsx"
    )