"""
test_integracao_433.py — Integracao: BCB 433 (IPCA) -> X-13 -> ARIMA -> projecao 5 anos.

Gera 4 arquivos em tests/output/:

  ipca_realizado.csv        — dado publico puro do BCB
                              colunas: data, valor
                              sep=;  decimal=,

  ipca_dessaz.csv           — serie historica: original + dessazonalizada (X-13)
                              colunas: data, valor, valor_dessaz
                              sep=;  decimal=,

  ipca_projecao_dessaz.csv  — historico + projecao ARIMA (60 meses)
                              colunas: data, valor, valor_dessaz, tipo
                              valor      = original (hist) / proj com sazonalidade (proj)
                              valor_dessaz = dessaz (hist) / proj ARIMA dessaz (proj)
                              tipo       = historico | projecao
                              sep=;  decimal=,

  ipca_residuo.csv          — residuo irregular do X-13 (s13)
                              colunas: data, valor
                              sep=,  decimal=.  (formato americano)

Requer conexao com a internet e binario X-13 instalado (x13.init()).
"""

import sys
import warnings
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import data_economist.bcb_sgs as bcb_sgs
import data_economist.x13 as x13

OUTPUT_DIR = Path(__file__).resolve().parent / "output"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def serie_ipca():
    """Baixa o IPCA (cod. 433) do BCB desde 2010. Retorna pd.Series mensal."""
    dados = bcb_sgs.get(433, "2010-01-01")
    df = pd.DataFrame(dados)
    df["data"] = pd.to_datetime(df["data"], format="%d/%m/%Y")
    serie = (
        df.set_index("data")["valor"]
        .astype(float)
        .resample("ME")
        .last()
        .dropna()
    )
    assert len(serie) >= 60, "Serie IPCA muito curta para dessazonalizar"
    return serie


@pytest.fixture(scope="module")
def modelo_x13(serie_ipca):
    """Roda o X-13ARIMA-SEATS na serie IPCA e devolve SeasonalResult."""
    raiz = Path(__file__).resolve().parent.parent
    x13.init(project_root=raiz)
    return x13.seas(serie_ipca, title="IPCA_433", transform_function="none")


# ---------------------------------------------------------------------------
# Teste principal
# ---------------------------------------------------------------------------

def test_ipca_433_gerar_csvs(serie_ipca, modelo_x13):
    """
    Fluxo completo:
    1. ipca_realizado.csv     — dado bruto (data, valor)
    2. ipca_dessaz.csv        — historico original + dessaz (data, valor, valor_dessaz)
    3. ipca_projecao_dessaz   — historico + projecao c/sazon e dessaz (data, valor, valor_dessaz, tipo)
    4. ipca_residuo.csv       — residuo irregular X-13 em formato americano (data, valor)
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    original  = x13.original(modelo_x13)
    dessaz    = x13.final(modelo_x13)
    irregular = x13.irregular(modelo_x13)

    assert dessaz is not None,    "X-13 nao retornou serie dessazonalizada"
    assert len(dessaz) == len(serie_ipca)

    n_hist = len(serie_ipca)

    # ------------------------------------------------------------------
    # 1. ipca_realizado.csv — data, valor
    # ------------------------------------------------------------------
    df_realizado = original.rename("valor").to_frame()
    df_realizado.index.name = "data"
    caminho_realizado = OUTPUT_DIR / "ipca_realizado.csv"
    df_realizado.to_csv(caminho_realizado, sep=";", decimal=",", encoding="utf-8-sig")

    # ------------------------------------------------------------------
    # 2. ipca_dessaz.csv — data, valor, valor_dessaz
    # ------------------------------------------------------------------
    df_dessaz = pd.DataFrame({
        "valor":       original,
        "valor_dessaz": dessaz,
    })
    df_dessaz.index.name = "data"
    caminho_dessaz = OUTPUT_DIR / "ipca_dessaz.csv"
    df_dessaz.to_csv(caminho_dessaz, sep=";", decimal=",", encoding="utf-8-sig")

    # ------------------------------------------------------------------
    # 3. ipca_projecao_dessaz.csv — data, valor, valor_dessaz, tipo
    #    Projecao ARIMA(1,1,1) sobre a serie dessaz (sem sazonalidade residual)
    #    valor_dessaz : projecao pura ARIMA
    #    valor        : projecao + fator sazonal medio por mes (re-sazonalizacao aditiva)
    # ------------------------------------------------------------------
    from statsmodels.tsa.arima.model import ARIMA

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        modelo_arima = ARIMA(dessaz, order=(1, 1, 1)).fit()

    steps    = 60  # 5 anos
    previsao = modelo_arima.forecast(steps=steps)

    ultimo  = dessaz.index[-1]
    idx_proj = pd.date_range(
        start=ultimo + pd.offsets.MonthEnd(1),
        periods=steps,
        freq="ME",
    )
    proj_dessaz = pd.Series(previsao.values, index=idx_proj)

    # Fator sazonal aditivo medio por mes (1..12)
    fator_sazonal = original - dessaz
    fator_sazonal.index = fator_sazonal.index.to_period("M")
    fator_por_mes = fator_sazonal.groupby(fator_sazonal.index.month).mean()

    proj_com_sazon = proj_dessaz.copy()
    proj_com_sazon.index = proj_com_sazon.index.to_period("M")
    proj_com_sazon = proj_com_sazon + proj_com_sazon.index.month.map(fator_por_mes)
    proj_com_sazon.index = proj_com_sazon.index.to_timestamp("M")

    # Historico: valor=original, valor_dessaz=dessaz
    df_hist = pd.DataFrame({
        "valor":        original,
        "valor_dessaz": dessaz,
        "tipo":         "historico",
    })

    # Projecao: valor=proj c/sazon, valor_dessaz=proj dessaz
    proj_com_sazon.index = idx_proj   # garantir mesmo indice
    df_proj = pd.DataFrame({
        "valor":        proj_com_sazon.values,
        "valor_dessaz": proj_dessaz.values,
        "tipo":         "projecao",
    }, index=idx_proj)

    df_proj_dessaz = pd.concat([df_hist, df_proj])
    df_proj_dessaz.index.name = "data"
    caminho_proj_dessaz = OUTPUT_DIR / "ipca_projecao_dessaz.csv"
    df_proj_dessaz.to_csv(caminho_proj_dessaz, sep=";", decimal=",", encoding="utf-8-sig")

    # ------------------------------------------------------------------
    # 4. ipca_residuo.csv — data, valor  (formato americano: sep=, decimal=.)
    # ------------------------------------------------------------------
    if irregular is not None:
        residuo = irregular.rename("valor")
    else:
        residuo = (original - dessaz).rename("valor")

    df_residuo = residuo.to_frame()
    df_residuo.index.name = "data"
    caminho_residuo = OUTPUT_DIR / "ipca_residuo.csv"
    df_residuo.to_csv(caminho_residuo, sep=",", decimal=".", encoding="utf-8-sig")

    # ------------------------------------------------------------------
    # Verificacoes
    # ------------------------------------------------------------------
    assert caminho_realizado.is_file()
    assert caminho_dessaz.is_file()
    assert caminho_proj_dessaz.is_file()
    assert caminho_residuo.is_file()

    df_r  = pd.read_csv(caminho_realizado,   sep=";", decimal=",", encoding="utf-8-sig", index_col=0)
    df_d  = pd.read_csv(caminho_dessaz,      sep=";", decimal=",", encoding="utf-8-sig", index_col=0)
    df_pd = pd.read_csv(caminho_proj_dessaz, sep=";", decimal=",", encoding="utf-8-sig", index_col=0)
    df_res = pd.read_csv(caminho_residuo,    sep=",", decimal=".", encoding="utf-8-sig", index_col=0)

    assert len(df_r)   == n_hist
    assert len(df_d)   == n_hist
    assert len(df_pd)  == n_hist + steps
    assert len(df_res) == n_hist

    assert list(df_r.columns)   == ["valor"]
    assert list(df_d.columns)   == ["valor", "valor_dessaz"]
    assert list(df_pd.columns)  == ["valor", "valor_dessaz", "tipo"]
    assert list(df_res.columns) == ["valor"]

    assert df_pd["tipo"].eq("projecao").sum()  == steps
    assert df_pd["tipo"].eq("historico").sum() == n_hist

    # ------------------------------------------------------------------
    # Resumo no terminal
    # ------------------------------------------------------------------
    ic_low  = float(modelo_arima.conf_int(alpha=0.05).iloc[-1, 0])
    ic_high = float(modelo_arima.conf_int(alpha=0.05).iloc[-1, 1])

    print("\n" + "=" * 64)
    print("  IPCA 433 - Dessazonalizacao e Projecao ARIMA(1,1,1)")
    print("=" * 64)
    print(f"  Observacoes historicas   : {n_hist}")
    print(f"  Periodo historico        : {original.index[0].date()} a {original.index[-1].date()}")
    print(f"  Ultimo IPCA (valor)      : {original.iloc[-1]:.4f} %")
    print(f"  Ultimo IPCA (dessaz)     : {dessaz.iloc[-1]:.4f} %")
    print(f"  Projecao                 : {idx_proj[0].date()} a {idx_proj[-1].date()} ({steps} meses)")
    print(f"  Proj. valor_dessaz final : {proj_dessaz.iloc[-1]:.4f} %")
    print(f"  Proj. valor final        : {proj_com_sazon.iloc[-1]:.4f} %"
          f"  IC 95%: [{ic_low:.4f}, {ic_high:.4f}]")
    print(f"  Fator sazonal jan (med)  : {fator_por_mes[1]:.4f} %")
    print("-" * 64)
    print(f"  {caminho_realizado.name:<38} {len(df_r):>4} linhas")
    print(f"  {caminho_dessaz.name:<38} {len(df_d):>4} linhas")
    print(f"  {caminho_proj_dessaz.name:<38} {len(df_pd):>4} linhas  ({n_hist} hist + {steps} proj)")
    print(f"  {caminho_residuo.name:<38} {len(df_res):>4} linhas  (formato americano)")
    print("=" * 64)
