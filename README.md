# 🌦️ Clima Pipeline — Data Engineering Project

> **Pipeline de dados climáticos ponta a ponta:** Ingestão de API pública, limpeza e tratamento de dados, agregações diárias, persistência relacional com batching, REST API de alta performance e dashboard analítico interativo.

---

## 👥 Integrantes do Projeto

| Nome | Matrícula |
| :--- | :---: |
| **Nilton Floriano** | `2600492` |
| **Murillo Alves Fração** | `2602143` |
| **Denner de Oliveira Duarte** | `2601848` |
| **Leonardo Barreto dos Santos** | `2602068` |
| **Vitor Alves Gameleira** | `2603000` |

---

## 📌 Sobre o Projeto

Este projeto foi desenvolvido como material didático e prático para cobrir todo o ciclo de vida da Engenharia de Dados em produção, utilizando dados meteorológicos históricos de **7 capitais brasileiras** representativas das 5 regiões do país:

* **Norte:** Manaus (AM) e Belém (PA)
* **Nordeste:** Recife (PE)
* **Sudeste:** São Paulo (SP) e Rio de Janeiro (RJ)
* **Sul:** Porto Alegre (RS) e Curitiba (PR)

O projeto está estruturado em duas camadas complementares:
1. **[`notebooks/`](notebooks/):** Exploração interativa passo a passo (análise exploratória, prototipação de limpeza, testes de visualização com Seaborn/Matplotlib e persistência com SQLite/SQLAlchemy).
2. **[`src/clima_pipeline/`](src/clima_pipeline/):** Pacote Python profissional com arquitetura modular, tipagem estática (*type hints*), tratamento de exceções robusto, logging estruturado, persistência otimizada em lotes (*batch upsert*), REST API com FastAPI e aplicação interativa com Streamlit.

---

## 🏗️ Arquitetura e Fluxo de Dados

```text
       [ Open-Meteo Historical API ]
                     │
                     ▼
  1. Extração (extract/open_meteo_client.py)
        • Sessão HTTP persistente (requests)
        • Coleta horária com salvamento de JSON bruto
                     │
                     ▼
  2. Limpeza & Tratamento (transform/cleaner.py)
        • Remoção de duplicatas
        • Interpolação linear de faltantes (temperatura, umidade e sensação)
        • Tratamento de outliers pelo método IQR (vento)
        • Padronização de schema para português
                     │
                     ▼
  3. Agregação Analítica (transform/aggregator.py & resumo.py)
        • Agregações diárias (médias, mínimos, máximos, totais de chuva)
        • Features derivadas: categorias térmicas, médias móveis (3d e 7d), ranking diário
        • Resumo do período com estatísticas consolidadas
                     │
                     ▼
  4. Persistência em Banco de Dados (load/sqlite_repository.py)
        • SQLAlchemy Core com schema declarativo
        • Inserção em lotes (batching) com UPSERT idempotente (ON CONFLICT DO UPDATE)
                     │
                     ▼
  5. Camada de Serviço — REST API (api/main.py)
        • FastAPI com contratos validados por schemas Pydantic
        • Documentação interativa automática (Swagger UI / OpenAPI)
                     │
                     ▼
  6. Visualização & Consumo — Dashboard (dashboard/app.py)
        • Streamlit desacoplado (consome apenas a API REST)
        • Cartões métricos do período, gráficos de linha comparativos e tabelas
```

---

## 📁 Estrutura do Repositório

```text
Projeto-Final-Python/
├── notebooks/                     # Exploração e aprendizado progressivo
│   ├── 01_extracao_open_meteo.ipynb
│   ├── 02_tratamento_pandas.ipynb
│   ├── 03_nova_visao_agregacoes.ipynb
│   ├── 04_exploracao_visual.ipynb
│   ├── 05_sqlite_persistencia.ipynb
│   └── 06_boas_praticas_python.ipynb
│
├── src/clima_pipeline/            # Código-fonte da aplicação modular
│   ├── config.py                  # Configurações globais, coordenadas e variáveis
│   ├── extract/                   # Camada de extração (OpenMeteoClient)
│   ├── transform/                 # Limpeza (Cleaner), Agregação e Resumo Analítico
│   │   ├── cleaner.py
│   │   ├── aggregator.py
│   │   └── resumo.py              # Cálculo de estatísticas consolidadas do período
│   ├── load/                      # Persistência relacional em SQLite com batching
│   │   └── sqlite_repository.py
│   ├── pipeline.py                # Orquestrador do pipeline (CLI)
│   ├── api/                       # REST API com FastAPI (main.py e schemas.py)
│   └── dashboard/                 # Interface gráfica com Streamlit (app.py)
│
├── data/                          # Armazenamento local
│   ├── raw/                       # Cópia bruta dos JSONs para auditoria
│   └── clima.db                   # Banco SQLite persistido
│
└── docs/                          # Documentação técnica com Sphinx
```

---

## ⚡ Guia Rápido de Execução

### 1. Preparação do Ambiente

Clone o repositório, crie e ative o ambiente virtual:

```bash
# Criar ambiente virtual
python -m venv .venv

# Ativar no Windows (PowerShell):
.venv\Scripts\activate

# Ativar no Linux/macOS:
source .venv/bin/activate

# Instalar o projeto em modo editável
pip install -e .
```

---

### 2. Executar o Pipeline de Dados

O pipeline se conecta ao Open-Meteo, extrai os dados das 7 cidades, realiza o tratamento, calcula as agregações diárias e persiste no SQLite:

```bash
python -m clima_pipeline.pipeline
```

*(Opcional: você também pode especificar cidades e datas customizadas)*:
```bash
python -m clima_pipeline.pipeline --cidades belem curitiba sao_paulo --inicio 2025-01-01 --fim 2025-01-31
```

---

### 3. Iniciar a REST API

Suba o servidor da API FastAPI:

```bash
uvicorn clima_pipeline.api.main:app --reload
```

Acesse a documentação interativa no navegador: **[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)**

#### Endpoints Principais:
| Método | Endpoint | Descrição |
| :--- | :--- | :--- |
| `GET` | `/health` | Checagem de disponibilidade da API |
| `GET` | `/cidades` | Listagem das 7 capitais cadastradas e coordenadas |
| `GET` | `/clima/diario` | Série temporal diária de uma cidade com filtro opcional de datas |
| `GET` | `/clima/resumo` | Resumo estatístico consolidado do período selecionado |

---

### 4. Executar o Dashboard Analítico

Em um novo terminal (mantendo a API rodando no primeiro), execute o Streamlit:

```bash
streamlit run src/clima_pipeline/dashboard/app.py
```

O dashboard abrirá em `http://localhost:8501`, permitindo:
- Seleção dinâmica de múltiplas cidades;
- Filtragem interativa por período;
- Visualização de cartões métricos com recordes e médias do período;
- Gráficos temporais de tendências e médias móveis (7 dias);
- Comparativo direto entre capitais para variáveis customizadas (temperatura, umidade, vento, sensação térmica).

---

## 🧪 Testes Unitários e Execução Isolada dos Módulos

Todos os módulos do projeto possuem testes com dados simulados (*mocks*) em seus blocos `__main__`, permitindo validação independente sem depender de conexões externas:

```bash
python -m clima_pipeline.config
python -m clima_pipeline.transform.cleaner
python -m clima_pipeline.transform.aggregator
python -m clima_pipeline.transform.resumo
python -m clima_pipeline.load.sqlite_repository
```

---

## 📚 Documentação Técnica (Sphinx)

Para compilar a documentação formal em HTML gerada a partir das *docstrings* do código:

```bash
pip install -e ".[docs]"
cd docs
make html
```

Os arquivos HTML serão gerados em `docs/_build/html/`.

---

<div align="center">
  <sub>MBA em Engenharia de Dados • Python Programming for Data Engineers</sub>
</div>
