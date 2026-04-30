import pandas as pd
import unicodedata
import os
import glob

# =========================
# 📥 CARREGAR TODOS OS ARQUIVOS
# =========================
arquivos = glob.glob("dados/bruto/queimadas_*.csv")

if not arquivos:
    raise Exception("❌ Nenhum arquivo encontrado em dados/bruto")

lista_df = []

for arq in arquivos:
    print(f"📂 Lendo: {arq}")
    try:
        df_temp = pd.read_csv(arq, encoding="utf-8")
    except:
        df_temp = pd.read_csv(arq, encoding="latin1")

    lista_df.append(df_temp)

df = pd.concat(lista_df, ignore_index=True)

# padronizar nomes das colunas
df.columns = df.columns.str.lower()

# =========================
# 🔍 DETECTAR COLUNA DATA
# =========================
def detectar_coluna_data(df):
    colunas = df.columns

    if "datahora" in colunas:
        return "datahora"
    elif "data" in colunas:
        return "data"
    elif "data_pas" in colunas:
        return "data_pas"
    else:
        print("⚠️ Colunas disponíveis:", df.columns)
        raise Exception("Nenhuma coluna de data encontrada")

col_data = detectar_coluna_data(df)

# =========================
# 📅 DATAS
# =========================
df["data"] = pd.to_datetime(df[col_data], errors="coerce")
df = df.dropna(subset=["data"])

df["mes"] = df["data"].dt.month
df["ano"] = df["data"].dt.year

# =========================
# 🧹 NORMALIZAÇÃO
# =========================
def normalizar(s):
    if pd.isna(s):
        return s
    s = str(s)
    s = unicodedata.normalize("NFKD", s)
    s = s.encode("ASCII", "ignore").decode("ASCII")
    return s.upper().strip()

if "estado" in df.columns:
    df["estado"] = df["estado"].apply(normalizar)

if "municipio" in df.columns:
    df["municipio"] = df["municipio"].apply(normalizar)

# =========================
# 🎯 FILTROS
# =========================
df_para = df[df["estado"].str.contains("PARA", na=False)] if "estado" in df.columns else pd.DataFrame()

df_obidos = df[df["municipio"].str.contains("OBIDOS", na=False)] if "municipio" in df.columns else pd.DataFrame()

# =========================
# 💾 SALVAR
# =========================
os.makedirs("dados/tratado", exist_ok=True)

df.to_csv("dados/tratado/queimadas_tratado.csv", index=False, encoding="utf-8")
df_para.to_csv("dados/tratado/para.csv", index=False, encoding="utf-8")
df_obidos.to_csv("dados/tratado/obidos.csv", index=False, encoding="utf-8")

# =========================
# 📊 DEBUG
# =========================
print("\n✅ Tratamento OK")
print("📅 Coluna de data usada:", col_data)
print("📊 Total de registros:", len(df))
print("📍 Estados únicos:", df["estado"].unique()[:10] if "estado" in df.columns else "N/A")
print("🔥 Registros Pará:", len(df_para))
print("🔥 Registros Óbidos:", len(df_obidos))