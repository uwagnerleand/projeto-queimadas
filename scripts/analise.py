import pandas as pd
import os

# =========================
# 📥 CARREGAR
# =========================
df = pd.read_csv("dados/tratado/queimadas_tratado.csv")

df["data"] = pd.to_datetime(df["data"], errors="coerce")
df = df.dropna(subset=["data"])

df["mes"] = df["data"].dt.month
df["ano"] = df["data"].dt.year

# =========================
# 🧹 NORMALIZAÇÃO EXTRA
# =========================
df["estado"] = df["estado"].astype(str).str.upper().str.strip()
df["municipio"] = df["municipio"].astype(str).str.upper().str.strip()

# =========================
# 🎯 FILTROS SEGUROS
# =========================
df_para = df[df["estado"].str.contains("PARA", na=False)]

df_obidos = df[df["municipio"] == "OBIDOS"]

# =========================
# 🏆 RANKING
# =========================
ranking = (
    df_para
    .groupby("municipio")
    .size()
    .sort_values(ascending=False)
    .reset_index(name="focos")
)

top10 = ranking.head(10)

print("\n🏆 Top 10 municípios:")
print(top10)

# =========================
# 📍 POSIÇÃO ÓBIDOS
# =========================
if "OBIDOS" in ranking["municipio"].values:
    posicao_obidos = ranking[ranking["municipio"] == "OBIDOS"].index[0] + 1
    print(f"\n📍 Óbidos está na posição {posicao_obidos}")
else:
    print("\n⚠️ Óbidos não encontrado no ranking")

# =========================
# 📊 PORCENTAGEM
# =========================
total_para = len(df_para)
total_obidos = len(df_obidos)

percentual = (total_obidos / total_para * 100) if total_para > 0 else 0

print(f"\n📊 Óbidos representa {percentual:.2f}% das queimadas do Pará")

# =========================
# 📈 SÉRIES TEMPORAIS
# =========================
serie_para = (
    df_para.groupby(["ano", "mes"])
    .size()
    .reset_index(name="focos")
)

serie_obidos = (
    df_obidos.groupby(["ano", "mes"])
    .size()
    .reset_index(name="focos")
)

# =========================
# 🔄 VARIAÇÃO (%)
# =========================
serie_para["variacao_%"] = serie_para["focos"].pct_change() * 100
serie_obidos["variacao_%"] = serie_obidos["focos"].pct_change() * 100

# eventos extremos
aumento_para = serie_para[serie_para["variacao_%"] > 30]
queda_para = serie_para[serie_para["variacao_%"] < -30]

aumento_obidos = serie_obidos[serie_obidos["variacao_%"] > 30]
queda_obidos = serie_obidos[serie_obidos["variacao_%"] < -30]

# =========================
# 📅 ANUAL
# =========================
anual_para = (
    df_para.groupby("ano")
    .size()
    .reset_index(name="focos")
)

anual_obidos = (
    df_obidos.groupby("ano")
    .size()
    .reset_index(name="focos")
)

# =========================
# 💾 SALVAR
# =========================
os.makedirs("outputs/analise", exist_ok=True)

ranking.to_csv("outputs/analise/ranking_municipios.csv", index=False)
top10.to_csv("outputs/analise/top10_municipios.csv", index=False)

serie_para.to_csv("outputs/analise/serie_para.csv", index=False)
serie_obidos.to_csv("outputs/analise/serie_obidos.csv", index=False)

anual_para.to_csv("outputs/analise/anual_para.csv", index=False)
anual_obidos.to_csv("outputs/analise/anual_obidos.csv", index=False)

aumento_para.to_csv("outputs/analise/aumento_para.csv", index=False)
queda_para.to_csv("outputs/analise/queda_para.csv", index=False)

aumento_obidos.to_csv("outputs/analise/aumento_obidos.csv", index=False)
queda_obidos.to_csv("outputs/analise/queda_obidos.csv", index=False)

print("\n✅ Análise concluída com sucesso")