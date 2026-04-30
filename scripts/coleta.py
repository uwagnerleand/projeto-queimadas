import pandas as pd
import requests
import zipfile
import io
import os

def detectar_coluna_data(df):
    if "datahora" in df.columns:
        return "datahora"
    elif "data" in df.columns:
        return "data"
    elif "data_pas" in df.columns:
        return "data_pas"
    else:
        print("⚠️ Colunas disponíveis:", df.columns)
        raise Exception("❌ Nenhuma coluna de data encontrada")


def carregar_dados_anual_zip(ano):
    url = f"https://dataserver-coids.inpe.br/queimadas/queimadas/focos/csv/anual/Brasil_sat_ref/focos_br_ref_{ano}.zip"

    print(f"🔄 Baixando {ano}...")

    response = requests.get(url)

    if response.status_code != 200:
        raise Exception(f"❌ Não foi possível baixar {ano}")

    zip_file = zipfile.ZipFile(io.BytesIO(response.content))

    arquivos = zip_file.namelist()
    print(f"📂 Arquivos no ZIP: {arquivos}")

    nome_csv = [f for f in arquivos if f.endswith(".csv")][0]

    print(f"📄 Usando arquivo: {nome_csv}")

    try:
        with zip_file.open(nome_csv) as f:
            df = pd.read_csv(f)
    except:
        with zip_file.open(nome_csv) as f:
            df = pd.read_csv(f, encoding="latin1")

    # =========================
    # 🔥 TRATAMENTO
    # =========================
    df.columns = df.columns.str.lower()

    if "estado" in df.columns:
        df["estado"] = df["estado"].astype(str).str.upper()

    if "municipio" in df.columns:
        df["municipio"] = df["municipio"].astype(str).str.upper()

    col_data = detectar_coluna_data(df)

    df["data"] = pd.to_datetime(df[col_data], errors="coerce")
    df = df.dropna(subset=["data"])

    df["mes"] = df["data"].dt.month
    df["ano"] = df["data"].dt.year

    print(f"✅ Dados carregados: {ano}")
    print(f"📊 Registros válidos: {len(df)}")

    return df


# =========================
# INPUT
# =========================
ano = input("Digite o ano (ex: 2024): ").strip()

df = carregar_dados_anual_zip(ano)

# =========================
# SALVAR (CORRETO)
# =========================
pasta = r"C:\Users\WIN10\Desktop\MONITORAMENTO\WAGNER\AUTOMATIZAÇÃO\projeto-queimadas\dados\bruto"
os.makedirs(pasta, exist_ok=True)

caminho = os.path.join(pasta, f"queimadas_{ano}.csv")

df.to_csv(caminho, index=False)

print(f"💾 Arquivo salvo em: {caminho}")