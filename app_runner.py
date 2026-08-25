"""
Inicializador do Dashboard Streamlit do Projeto Queimadas.

Executa o servidor local e abre o navegador automaticamente na porta configurada.
"""

from __future__ import annotations

import socket
import subprocess
import sys
import time
import webbrowser

PORTA_PADRAO = 8501


def porta_em_uso(porta: int = PORTA_PADRAO) -> bool:
    """Verifica se a porta local especificada já está ocupada por algum processo."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("localhost", porta)) == 0


def main() -> None:
    """Inicia a aplicação Streamlit e gerencia a sessão no navegador."""
    url = f"http://localhost:{PORTA_PADRAO}"
    if porta_em_uso(PORTA_PADRAO):
        print(f"✅ Aplicação já em execução em: {url}")
        webbrowser.open(url)
        return

    print("🚀 Inicializando o Dashboard Streamlit...")
    processo = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "dashboard/app.py", "--server.headless=true"]
    )

    time.sleep(3)
    webbrowser.open(url)
    print(f"✨ Dashboard aberto no navegador: {url}")
    print("Pressione Ctrl+C para encerrar o servidor.")

    try:
        processo.wait()
    except KeyboardInterrupt:
        print("\nEncerrando servidor Streamlit...")
        processo.terminate()


if __name__ == "__main__":
    main()
