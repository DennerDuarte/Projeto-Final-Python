"""Calcula o resumo do período (estatísticas) a partir da visão diária de uma cidade."""

import datetime as dt

import pandas as pd


def calcular_resumo(df_diario: pd.DataFrame) -> dict:
    """Recebe a visão diária de UMA cidade e devolve um dicionário com o resumo do período."""
    # idxmax() devolve o índice onde está o maior valor.
    # Com esse índice, df.loc[linha, "data"] pega a data daquela linha.
    linha_mais_quente = df_diario["temp_max"].idxmax()
    linha_mais_fria = df_diario["temp_min"].idxmin()

    return {
        "cidade": df_diario["cidade"].iloc[0],  # iloc[0] = valor da primeira linha
        "inicio": df_diario["data"].min(),
        "fim": df_diario["data"].max(),
        "dias_analisados": len(df_diario),
        "temp_media_periodo": round(float(df_diario["temp_media"].mean()), 1),
        "temp_max_absoluta": round(float(df_diario["temp_max"].max()), 1),
        "dia_mais_quente": df_diario.loc[linha_mais_quente, "data"],
        "temp_min_absoluta": round(float(df_diario["temp_min"].min()), 1),
        "dia_mais_frio": df_diario.loc[linha_mais_fria, "data"],
        "precipitacao_total_periodo": round(float(df_diario["precipitacao_total"].sum()), 1),
        "dias_chuvosos": int((df_diario["categoria_chuva"] == "chuvoso").sum()),
        "sensacao_media_periodo": round(float(df_diario["sensacao_media"].mean()), 1),
        "categoria_predominante": str(df_diario["categoria_temp"].value_counts().idxmax()),
    }


if __name__ == "__main__":
    # Entrada mockada: 4 dias inventados de Recife, para testar calcular_resumo()
    # sem precisar da API nem do banco.
    df_mock = pd.DataFrame({
        "cidade": ["recife"] * 4,
        "data": [dt.date(2025, 1, 1), dt.date(2025, 1, 2), dt.date(2025, 1, 3), dt.date(2025, 1, 4)],
        "temp_media": [26.0, 27.0, 29.0, 28.0],
        "temp_min": [23.0, 22.5, 25.0, 24.0],
        "temp_max": [30.0, 31.0, 34.5, 32.0],
        "precipitacao_total": [0.0, 12.5, 0.0, 3.0],
        "categoria_chuva": ["seco", "chuvoso", "seco", "chuvoso"],
        "sensacao_media": [28.0, 29.5, 32.0, 30.5],
        "categoria_temp": ["quente", "quente", "quente", "quente"],
    })
    print(calcular_resumo(df_mock))

