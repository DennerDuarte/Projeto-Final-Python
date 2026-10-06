"""REST API (FastAPI) para consultar o clima persistido em SQLite.

Esta API NÃO roda o pipeline nem fala com a Open-Meteo — ela só lê o que o
pipeline (pipeline.py) já deixou salvo em data/clima.db. Se o banco estiver
vazio (pipeline nunca rodou), os endpoints simplesmente devolvem listas
vazias, sem erro.

A API tem 3 endpoints de dado (fora /health): listar cidades, consultar a
visão diária de UMA cidade por vez e consultar o resumo do período (/clima/resumo).
Qualquer comparação entre cidades (gráficos, tabelas) é montada no dashboard a
partir desses mesmos dados.
"""

import datetime as dt
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import RedirectResponse
import pandas as pd

from clima_pipeline.api.schemas import CidadeOut, ClimaDiarioOut, HealthOut, ResumoOut
# Importar config aqui já deixa o logging configurado (veja o
# logging.basicConfig no fim de config.py) — nenhuma chamada extra é
# necessária.
from clima_pipeline.config import CIDADES, resolver_slug_cidade
from clima_pipeline.load import SQLiteRepository
from clima_pipeline.transform import calcular_resumo

# Uma única instância de SQLiteRepository para a vida inteira do processo da
# API — criada aqui, na importação do módulo (então qualquer erro de conexão
# com o banco aparece já na subida da API, não só no primeiro request).
# Todos os endpoints abaixo reaproveitam esta mesma instância em vez de abrir
# uma conexão nova a cada requisição.
_repositorio = SQLiteRepository()


def get_repository() -> SQLiteRepository:
    """Devolve a instância única de SQLiteRepository usada por toda a API."""
    return _repositorio


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Código que roda no início e no fim da vida da API.

    Tudo antes do `yield` roda quando a API sobe; tudo depois roda quando a
    API é encerrada (aqui, fecha a conexão com o banco). O FastAPI chama isso
    automaticamente — não precisamos invocar lifespan() em lugar nenhum.
    """
    yield
    get_repository().dispose()


app = FastAPI(
    title="Clima Pipeline API",
    description="Consulta dados climáticos históricos tratados e agregados.",
    version="0.1.0",
    lifespan=lifespan,
)


def _resolver_ou_404(identificador: str) -> str:
    """Traduz o texto recebido (slug/nome/UF) em slug, ou já lança o erro HTTP certo."""
    slug = resolver_slug_cidade(identificador)
    if slug is None:
        raise HTTPException(
            status_code=404,
            detail=f"Cidade '{identificador}' não encontrada. Use /cidades para ver as opções.",
        )
    return slug

def _filtrar_periodo(df: pd.DataFrame, inicio: dt.date | None, fim: dt.date | None) -> pd.DataFrame:
    """Mantém só as linhas entre `inicio` e `fim` (os dois são opcionais)."""
    df["data"] = df["data"].dt.date  # converte data+hora em só data, para comparar com inicio/fim
    if inicio:
        df = df[df["data"] >= inicio]
    if fim:
        df = df[df["data"] <= fim]
    return df


@app.get("/", include_in_schema=False)
def raiz() -> RedirectResponse:
    """Quem acessar a raiz da API cai direto na documentação interativa (Swagger UI)."""
    return RedirectResponse(url="/docs")


@app.get("/health", response_model=HealthOut)
def health() -> HealthOut:
    """Endpoint simples para checar se a API está no ar (usado por monitoramento, load balancer, etc.)."""
    return HealthOut()


@app.get("/cidades", response_model=list[CidadeOut])
def listar_cidades() -> list[CidadeOut]:
    """Lista as cidades cadastradas em config.CIDADES — não depende do banco."""
    return [
        CidadeOut(slug=slug, nome_exibicao=info["nome_exibicao"], uf=info["uf"],
                   regiao=info["regiao"], lat=info["lat"], lon=info["lon"])
        for slug, info in CIDADES.items()
    ]


@app.get("/clima/diario", response_model=list[ClimaDiarioOut])
def clima_diario(
    cidade: str = Query(..., description="Slug, nome de exibição ou UF da cidade"),
    inicio: dt.date | None = Query(None, description="Data inicial (YYYY-MM-DD)"),
    fim: dt.date | None = Query(None, description="Data final (YYYY-MM-DD)"),
) -> list[ClimaDiarioOut]:
    """Devolve a visão diária de uma cidade, com filtro opcional de período.

    Único endpoint de dado climático da API — para comparar várias cidades,
    o dashboard chama este endpoint uma vez por cidade e junta os resultados
    (veja dashboard/app.py).
    """
    slug = _resolver_ou_404(cidade)
    df = get_repository().get_daily(city=slug)

    if df.empty:
        return []

    # inicio/fim são opcionais (Query(None, ...)) — só filtra se o cliente
    # da API de fato informou o parâmetro.
    df = _filtrar_periodo(df, inicio, fim)

    # **row desempacota o dict da linha como argumentos nomeados do
    # construtor do Pydantic — dict {"cidade": "sp", "temp_media": 24.1, ...}
    # vira ClimaDiarioOut(cidade="sp", temp_media=24.1, ...).
    return [ClimaDiarioOut(**row) for row in df.to_dict(orient="records")]


@app.get("/clima/resumo", response_model=ResumoOut)
def clima_resumo(
    cidade: str = Query(..., description="Slug, nome de exibição ou UF da cidade"),
    inicio: dt.date | None = Query(None, description="Data inicial (YYYY-MM-DD)"),
    fim: dt.date | None = Query(None, description="Data final (YYYY-MM-DD)"),
) -> ResumoOut:
    """Devolve o resumo do período (dia mais quente, total de chuva, etc.) de uma cidade."""
    # 1) resolve a cidade ou lança erro 404
    slug = _resolver_ou_404(cidade)

    # 2) busca a visão diária no banco
    df = get_repository().get_daily(city=slug)

    # 3) se a cidade não tem dados no banco, erro 404
    if df.empty:
        raise HTTPException(status_code=404, detail="Sem dados para o período informado.")

    # 4) filtra pelo período solicitado
    df = _filtrar_periodo(df, inicio, fim)

    # 5) se após o filtro não sobrou nenhum registro, erro 404
    if df.empty:
        raise HTTPException(status_code=404, detail="Sem dados para o período informado.")

    # 6) calcula o resumo e devolve validado pelo schema ResumoOut
    resumo = calcular_resumo(df)
    return ResumoOut(**resumo)