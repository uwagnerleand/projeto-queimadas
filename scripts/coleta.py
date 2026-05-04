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


def normalizar_json(data):
    if isinstance(data, list):
        return pd.json_normalize(data)

    if isinstance(data, dict):
        if "data" in data and isinstance(data["data"], list):
            return pd.json_normalize(data["data"])

        if len(data) == 1:
            item = next(iter(data.values()))
            if isinstance(item, list):
                return pd.json_normalize(item)

        return pd.json_normalize(data)

    raise ValueError("Formato JSON inesperado. A resposta deve conter uma lista ou um objeto JSON.")


def carregar_dados_api_json(url):
    print(f"🔄 Baixando dados da API: {url}")
    response = requests.get(url, timeout=30)
    response.raise_for_status()

    data = response.json()
    df = normalizar_json(data)

    print(f"✅ Dados carregados da API: {len(df)} registros")
    return df


def carregar_dados_anual_zip(ano):
    url = f"https://dataserver-coids.inpe.br/queimadas/queimadas/focos/csv/anual/Brasil_sat_ref/focos_br_ref_{ano}.zip"

    print(f"🔄 Baixando {ano}...")

    response = requests.get(url, timeout=60)
    response.raise_for_status()

    zip_file = zipfile.ZipFile(io.BytesIO(response.content))

    arquivos = zip_file.namelist()
    print(f"📂 Arquivos no ZIP: {arquivos}")

    nome_csv = [f for f in arquivos if f.endswith(".csv")][0]

    print(f"📄 Usando arquivo: {nome_csv}")

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

    col_data = detectar_coluna_data(df)
    df["data"] = pd.to_datetime(df[col_data], errors="coerce")
    df = df.dropna(subset=["data"])

    df["mes"] = df["data"].dt.month
    df["ano"] = df["data"].dt.year

    print(f"✅ Dados carregados: {ano}")
    print(f"📊 Registros válidos: {len(df)}")

    return df


def salvar_dataframe(df, nome_arquivo):
    raiz = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    pasta = os.path.join(raiz, "dados", "bruto")
    os.makedirs(pasta, exist_ok=True)

    caminho = os.path.join(pasta, f"{nome_arquivo}.csv")
    df.to_csv(caminho, index=False)
    print(f"💾 Arquivo salvo em: {caminho}")


if __name__ == "__main__":
    fonte = input("Escolha a fonte de dados [inpe/ibge]: ").strip().lower()

    if fonte == "ibge":
        url = input("Digite a URL da API IBGE (ou outra API JSON): ").strip()
        if not url:
            raise ValueError("A URL não pode ficar vazia.")
        df = carregar_dados_api_json(url)
        nome_arquivo = "queimadas_ibge"
    elif fonte == "inpe":
        ano = input("Digite o ano (ex: 2024): ").strip()
        if not ano.isdigit():
            raise ValueError("Ano inválido. Use apenas números.")
        df = carregar_dados_anual_zip(ano)
        nome_arquivo = f"queimadas_{ano}"
    else:
        raise ValueError("Fonte inválida. Escolha 'inpe' ou 'ibge'.")

    salvar_dataframe(df, nome_arquivo)
