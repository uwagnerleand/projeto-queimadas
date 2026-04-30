import subprocess
import webbrowser
import time
import socket
import sys

PORTA = 8501

def porta_em_uso(port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    resultado = s.connect_ex(("localhost", port))
    s.close()
    return resultado == 0

# se já estiver rodando, só abre o navegador
if porta_em_uso(PORTA):
    webbrowser.open(f"http://localhost:{PORTA}")
    print("App já estava rodando.")
else:
    print("Iniciando Streamlit...")

    subprocess.Popen([
        sys.executable, "-m", "streamlit", "run", "dashboard/app.py",
        "--server.headless=true"
    ])

    time.sleep(3)
    webbrowser.open(f"http://localhost:{PORTA}")

input("Pressione ENTER para fechar...")