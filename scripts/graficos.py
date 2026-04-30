import pandas as pd
import matplotlib.pyplot as plt
import os
import seaborn as sns

# =========================
# 📥 CARREGAR
# =========================
df = pd.read_csv("dados/tratado/queimadas_tratado.csv")

df["data"] = pd.to_datetime(df["data"], errors="coerce")
df = df.dropna(subset=["data"])

df["mes"] = df["data"].dt.month
df["ano"] = df["data"].dt.year

# padronização
df["estado"] = df["estado"].astype(str).str.upper().str.strip()
df["municipio"] = df["municipio"].astype(str).str.upper().str.strip()

# =========================
# 🎯 FILTROS
# =========================
df_para = df[df["estado"].str.contains("PARA", na=False)]
df_obidos = df[df["municipio"] == "OBIDOS"]

# =========================
# 📁 PASTA
# =========================
os.makedirs("outputs/graficos", exist_ok=True)

# =========================
# 📊 FUNÇÃO BASE
# =========================
def salvar_barra(serie, titulo, caminho, xlabel="Mês"):
    fig, ax = plt.subplots(figsize=(10, 5))
    serie.plot(kind="bar", ax=ax)

    ax.set_title(titulo)
    ax.set_xlabel(xlabel)
    ax.set_ylabel("Quantidade")

    for p in ax.patches:
        altura = p.get_height()
        if altura > 0:
            ax.annotate(
                str(int(altura)),
                (p.get_x() + p.get_width() / 2, altura),
                ha='center',
                va='bottom',
                fontsize=8
            )

    plt.tight_layout()
    plt.savefig(caminho)
    plt.close()

# =========================
# 📊 ÓBIDOS - MENSAL
# =========================
if not df_obidos.empty:

    anos = sorted(df_obidos["ano"].unique())

    for ano in anos:

        df_ano = df_obidos[df_obidos["ano"] == ano]

        grafico = (
            df_ano.groupby("mes")
            .size()
            .reindex(range(1,13), fill_value=0)
        )

        salvar_barra(
            grafico,
            f"Focos por mês - Óbidos ({ano})",
            f"outputs/graficos/obidos_mensal_{ano}.png"
        )
# =========================
# 📈 EVOLUÇÃO ÓBIDOS
# =========================
if not df_obidos.empty:

    serie = df_obidos.groupby(["ano","mes"]).size().reset_index(name="focos")

    serie["data"] = pd.to_datetime(
        serie["ano"].astype(str) + "-" + serie["mes"].astype(str)
    )

    serie = serie.sort_values("data")

    plt.figure(figsize=(10,5))
    plt.plot(serie["data"], serie["focos"], marker="o")

    plt.title("Evolução geral - Óbidos")
    plt.xlabel("Data")
    plt.ylabel("Focos")

    plt.tight_layout()
    plt.savefig("outputs/graficos/obidos_evolucao.png")
    plt.close()

# =========================
# 📉 VARIAÇÃO (%)
# =========================
if not df_obidos.empty:

    anos = sorted(df_obidos["ano"].unique())

    for ano in anos:

        df_ano = df_obidos[df_obidos["ano"] == ano]

        serie = (
            df_ano.groupby("mes")
            .size()
            .reindex(range(1,13), fill_value=0)
        )

        variacao = serie.pct_change() * 100

        plt.figure(figsize=(10,5))
        plt.plot(serie.index, variacao, marker="o")

        plt.axhline(0)
        plt.title(f"Variação percentual - Óbidos ({ano})")
        plt.xlabel("Mês")
        plt.ylabel("%")

        plt.tight_layout()
        plt.savefig(f"outputs/graficos/obidos_variacao_{ano}.png")
        plt.close()

# =========================
# 📅 ANUAL
# =========================
if not df_obidos.empty:

    anual = df_obidos.groupby("ano").size().sort_index()

    salvar_barra(
        anual,
        "Focos por ano - Óbidos",
        "outputs/graficos/obidos_anual.png",
        "Ano"
    )

# =========================
# 🔥 HEATMAP
# =========================
if not df_obidos.empty:
    tabela = df_obidos.groupby(["ano","mes"]).size().unstack(fill_value=0)
    tabela = tabela.reindex(columns=range(1,13), fill_value=0)

    plt.figure(figsize=(12,4))
    sns.heatmap(tabela, annot=True, fmt=".0f", cmap="YlOrRd")

    plt.title("Heatmap de queimadas - Óbidos")
    plt.xlabel("Mês")
    plt.ylabel("Ano")

    plt.savefig("outputs/graficos/obidos_heatmap.png")
    plt.close()

# =========================
# 🏆 RANKING MUNICIPAL
# =========================
if not df_para.empty:

    anos = sorted(df_para["ano"].unique())

    for ano in anos:

        df_ano = df_para[df_para["ano"] == ano]

        ranking = df_ano.groupby("municipio").size().sort_values(ascending=False)
        top10 = ranking.head(10)

        salvar_barra(
            top10,
            f"Top 10 municípios - Pará ({ano})",
            f"outputs/graficos/top10_{ano}.png",
            "Município"
        )

# =========================
# 📈 COMPARAÇÃO POR ANO (MUITO MAIS CLARO)
# =========================
if not df_para.empty:

    ranking = df_para.groupby("municipio").size().sort_values(ascending=False)
    top5 = ranking.head(5).index.tolist()

    # garantir OBIDOS
    if "OBIDOS" not in top5:
        top5.append("OBIDOS")

    anos_disponiveis = sorted(df_para["ano"].unique())

    for ano in anos_disponiveis:

        df_ano = df_para[df_para["ano"] == ano]

        plt.figure(figsize=(10,5))

        for municipio in top5:
            df_mun = df_ano[df_ano["municipio"] == municipio]

            serie = (
                df_mun.groupby("mes")
                .size()
                .reindex(range(1,13), fill_value=0)
            )

            plt.plot(serie.index, serie.values, marker="o", label=municipio)

        plt.title(f"Evolução mensal por município - {ano}")
        plt.xlabel("Mês")
        plt.ylabel("Focos")
        plt.legend()

        plt.tight_layout()
        plt.savefig(f"outputs/graficos/comparacao_{ano}.png")
        plt.close()

print("✅ Gráficos corrigidos e mais profissionais gerados")