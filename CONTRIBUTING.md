# Guia de Contribuição – Projeto Queimadas 🌿

Obrigado pelo seu interesse em contribuir para o **Projeto Queimadas**! Este projeto é voltado para o monitoramento, análise e geração de inteligência sobre focos de queimadas no território brasileiro.

---

## 🛠️ Como Começar

### 1. Clonar e Configurar o Ambiente
```bash
# Clone o repositório
git clone https://github.com/uwagnerleand/projeto-queimadas.git
cd projeto-queimadas

# Crie e ative um ambiente virtual
python3 -m venv .venv
source .venv/bin/activate  # No Windows: .venv\Scripts\activate

# Instale as dependências de desenvolvimento
make dev-install
# ou: pip install -r requirements.txt && pip install pytest pytest-cov ruff
```

### 2. Padrões de Código e Qualidade
Utilizamos o **Ruff** para linting e formatação e o **Pytest** para testes unitários:

```bash
# Verificar linting
make lint

# Formatar o código
make format

# Executar a suíte de testes
make test
```

---

## 📌 Fluxo de Branches e Commits

1. Crie uma branch descritiva a partir da `main`:
   ```bash
   git checkout -b feature/sua-feature
   # ou: git checkout -b fix/seu-ajuste
   ```
2. Utilize o padrão **Conventional Commits**:
   - `feat: adiciona novo filtro por bioma`
   - `fix: corrige cálculo de variação percentual`
   - `docs: atualiza instruções no README`
   - `refactor: modulariza script de gráficos`
   - `test: adiciona testes para módulo de coleta`

3. Certifique-se de que todos os testes passem antes de enviar o Pull Request:
   ```bash
   pytest tests/ -v
   ```

4. Abra seu Pull Request detalhando as mudanças realizadas e o motivo da alteração.

---

## 📬 Dúvidas ou Sugestões?
Abra uma [Issue no GitHub](https://github.com/uwagnerleand/projeto-queimadas/issues) ou entre em contato com os mantenedores.
