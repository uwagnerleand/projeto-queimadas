import streamlit as st
import pandas as pd
import os
import folium
from streamlit_folium import st_folium
from io import BytesIO

st.set_page_config(page_title="Queimadas", layout="wide")

# =========================
# 📥 CARREGAR DADOS
# =========================
@st.cache_data
def carregar_dados():
    df = pd.read_csv("dados/tratado/queimadas_tratado.csv")

    # normalizar colunas de coordenadas
    df = df.rename(columns={
        "lat": "latitude",
        "lon": "longitude"
    })

    # datas
    df["data"] = pd.to_datetime(df["data"], errors="coerce")
    df = df.dropna(subset=["data"])

    df["mes"] = df["data"].dt.month
    df["ano"] = df["data"].dt.year

    # texto
    df["municipio"] = df["municipio"].astype(str).str.upper().str.strip()
    df["estado"] = df["estado"].astype(str).str.upper().str.strip()

    return df

df = carregar_dados()

# =========================
# 🎛️ FILTROS (CORRIGIDO)
# =========================
st.sidebar.header("Filtros")

# ESTADO
estados = sorted(df["estado"].dropna().unique())
estado_sel = st.sidebar.selectbox(
    "Estado",
    estados,
    key="estado"
)

# filtrar estado
df_estado = df[df["estado"] == estado_sel]

# MUNICÍPIO (dependente do estado)
municipios = sorted(df_estado["municipio"].dropna().unique())
municipio_sel = st.sidebar.selectbox(
    "Município",
    municipios,
    key="municipio"
)

# ANO (dependente do estado)
anos = sorted(df_estado["ano"].dropna().unique())
ano_sel = st.sidebar.selectbox(
    "Ano",
    anos,
    key="ano"
)

# FILTRO FINAL
df_filtrado = df[
    (df["estado"] == estado_sel) &
    (df["municipio"] == municipio_sel) &
    (df["ano"] == ano_sel)
]

# =========================
# 🧠 TÍTULO
# =========================
st.markdown(f"""
# 🔥 Queimadas - {municipio_sel} ({estado_sel}) - {ano_sel}
""")

# =========================
# 📊 MÉTRICAS
# =========================
col1, col2, col3 = st.columns(3)

total_focos = len(df_filtrado)
media_mensal = df_filtrado.groupby("mes").size().mean() if not df_filtrado.empty else 0

df_estado_ano = df[
    (df["estado"] == estado_sel) &
    (df["ano"] == ano_sel)
]

total_estado = len(df_estado_ano)
percentual = (total_focos / total_estado * 100) if total_estado > 0 else 0

col1.metric("Total de focos", total_focos)
col2.metric("Média mensal", f"{media_mensal:.1f}")
col3.metric(f"% no estado", f"{percentual:.2f}%")

# =========================
# 📊 GRÁFICO MENSAL
# =========================
st.subheader("📊 Focos por mês")

if not df_filtrado.empty:
    grafico = df_filtrado.groupby("mes").size().reindex(range(1,13), fill_value=0)
    st.bar_chart(grafico)
else:
    st.warning("Sem dados")

# =========================
# 📈 EVOLUÇÃO
# =========================
st.subheader("📈 Evolução histórica")

df_evolucao = df[
    (df["estado"] == estado_sel) &
    (df["municipio"] == municipio_sel)
]

serie = df_evolucao.groupby(["ano","mes"]).size().reset_index(name="focos")

if not serie.empty:
    serie["data"] = pd.to_datetime(
        serie["ano"].astype(str) + "-" + serie["mes"].astype(str)
    )
    st.line_chart(serie.set_index("data")["focos"])
else:
    st.warning("Sem dados")

# =========================
# 🗺️ MAPA (ROBUSTO)
# =========================
st.subheader("🗺️ Mapa de focos")

# tenta diferentes nomes de colunas
possiveis_lat = ["latitude", "lat", "lat_gd"]
possiveis_lon = ["longitude", "lon", "long"]

lat_col = next((c for c in possiveis_lat if c in df.columns), None)
lon_col = next((c for c in possiveis_lon if c in df.columns), None)

if lat_col and lon_col:

    df_mapa = df_filtrado.dropna(subset=[lat_col, lon_col])

    if not df_mapa.empty:

        m = folium.Map(
            location=[df_mapa[lat_col].mean(), df_mapa[lon_col].mean()],
            zoom_start=7
        )

        for _, row in df_mapa.iterrows():
            folium.CircleMarker(
                location=[row[lat_col], row[lon_col]],
                radius=3,
                color="red",
                fill=True,
                fill_opacity=0.7
            ).add_to(m)

        st_folium(m, width=900, height=500)

    else:
        st.warning("Sem coordenadas válidas")

else:
    st.error("Colunas de coordenadas não encontradas")

# =========================
# 🏆 RANKING
# =========================
st.subheader("🏆 Ranking")

ranking = df_estado_ano.groupby("municipio").size().sort_values(ascending=False)
st.bar_chart(ranking.head(10))

if municipio_sel in ranking.index:
    pos = ranking.index.get_loc(municipio_sel) + 1
    st.info(f"{municipio_sel} está na posição #{pos}")

# =========================
# 📥 EXPORTAÇÃO EXCEL
# =========================
st.subheader("📥 Exportar")

def gerar_excel():
    output = BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:

        df_filtrado.to_excel(writer, sheet_name="Dados", index=False)

        df_filtrado.groupby("mes").size().to_excel(writer, sheet_name="Mensal")

        ranking.to_excel(writer, sheet_name="Ranking")

    return output.getvalue()

st.download_button(
    "Baixar Excel",
    data=gerar_excel(),
    file_name=f"queimadas_{municipio_sel}_{ano_sel}.xlsx"
)

# =========================
# 📄 DADOS
# =========================
st.subheader("📄 Dados")
st.dataframe(df_filtrado)