"""
test_modelos.py — Testes estruturais e de tipo para o módulo modelos.

Verificações:
- Todas as funções retornam o tipo correto
- Campos obrigatórios presentes em cada resultado
- Comprimentos de residuos/fitted coerentes com a série
- prever() retorna PrevisaoResult com número correto de steps
- Tratamento de erros (série inválida)
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from data_economist.modelos import (
    ModeloResult, PrevisaoResult, RaizResult, ACFResult,
    ar, ma, arma, arima, sarima, armax, prever,
    auto_arima, criterios, acf_pacf,
    adf, pp, kpss, za,
    arfima, gph,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def serie_ar1():
    """Série AR(1) estacionária sintética (phi=0.6)."""
    rng = np.random.default_rng(42)
    T = 120
    y = np.zeros(T)
    for t in range(1, T):
        y[t] = 0.5 + 0.6 * y[t - 1] + rng.normal(0, 1)
    idx = pd.date_range("2010-01", periods=T, freq="ME")
    return pd.Series(y, index=idx, name="ar1")


@pytest.fixture(scope="module")
def serie_passeiro():
    """Passeio aleatório (não estacionário)."""
    rng = np.random.default_rng(7)
    T = 120
    y = np.cumsum(rng.normal(0, 1, T))
    idx = pd.date_range("2010-01", periods=T, freq="ME")
    return pd.Series(y, index=idx, name="rw")


@pytest.fixture(scope="module")
def serie_sazonal():
    """Série com sazonalidade mensal (m=12) e tendência."""
    rng = np.random.default_rng(99)
    T = 120
    t = np.arange(T)
    y = 0.02 * t + np.sin(2 * np.pi * t / 12) + rng.normal(0, 0.3, T)
    idx = pd.date_range("2010-01", periods=T, freq="ME")
    return pd.Series(y, index=idx, name="sazonal")


# ---------------------------------------------------------------------------
# Testes — ar()
# ---------------------------------------------------------------------------

class TestAR:
    def test_retorna_tipo(self, serie_ar1):
        res = ar(serie_ar1, lags=1)
        assert isinstance(res, ModeloResult)

    def test_campos_obrigatorios(self, serie_ar1):
        res = ar(serie_ar1, lags=1)
        assert isinstance(res.params, pd.Series)
        assert isinstance(res.pvalues, pd.Series)
        assert isinstance(res.residuos, pd.Series)
        assert isinstance(res.fitted, pd.Series)
        assert isinstance(res.aic, float)
        assert isinstance(res.bic, float)
        assert res.nobs > 0

    def test_modelo_nome(self, serie_ar1):
        res = ar(serie_ar1, lags=2)
        assert "AR" in res.modelo

    def test_serie_invalida_curta(self):
        s = pd.Series([1.0, 2.0, 3.0])
        with pytest.raises((ValueError, Exception)):
            ar(s, lags=1)

    def test_serie_invalida_tipo(self):
        with pytest.raises(TypeError):
            ar([1, 2, 3, 4, 5] * 10, lags=1)


# ---------------------------------------------------------------------------
# Testes — ma()
# ---------------------------------------------------------------------------

class TestMA:
    def test_retorna_tipo(self, serie_ar1):
        res = ma(serie_ar1, lags=1)
        assert isinstance(res, ModeloResult)

    def test_campos_presentes(self, serie_ar1):
        res = ma(serie_ar1, lags=1)
        assert hasattr(res, "aic")
        assert hasattr(res, "residuos")
        assert "MA" in res.modelo


# ---------------------------------------------------------------------------
# Testes — arma()
# ---------------------------------------------------------------------------

class TestARMA:
    def test_retorna_tipo(self, serie_ar1):
        res = arma(serie_ar1, p=1, q=1)
        assert isinstance(res, ModeloResult)

    def test_ordem_correta(self, serie_ar1):
        res = arma(serie_ar1, p=2, q=1)
        assert res.ordem == (2, 0, 1)

    def test_aic_e_float(self, serie_ar1):
        res = arma(serie_ar1, p=1, q=1)
        assert not np.isnan(res.aic)


# ---------------------------------------------------------------------------
# Testes — arima()
# ---------------------------------------------------------------------------

class TestARIMA:
    def test_retorna_tipo(self, serie_passeiro):
        res = arima(serie_passeiro, p=1, d=1, q=1)
        assert isinstance(res, ModeloResult)

    def test_campos_obrigatorios(self, serie_passeiro):
        res = arima(serie_passeiro, p=1, d=1, q=0)
        assert len(res.residuos) > 0
        assert len(res.fitted) > 0

    def test_ordem_armazenada(self, serie_passeiro):
        res = arima(serie_passeiro, p=2, d=1, q=1)
        assert res.ordem == (2, 1, 1)

    def test_nome_modelo(self, serie_passeiro):
        res = arima(serie_passeiro, p=1, d=1, q=1)
        assert "ARIMA" in res.modelo


# ---------------------------------------------------------------------------
# Testes — sarima()
# ---------------------------------------------------------------------------

class TestSARIMA:
    def test_retorna_tipo(self, serie_sazonal):
        res = sarima(serie_sazonal, 1, 0, 1, 1, 0, 1, 12)
        assert isinstance(res, ModeloResult)

    def test_ordem_7_elementos(self, serie_sazonal):
        res = sarima(serie_sazonal, 1, 0, 1, 0, 0, 1, 12)
        assert len(res.ordem) == 7

    def test_nome_modelo(self, serie_sazonal):
        res = sarima(serie_sazonal, 1, 0, 1, 1, 0, 1, 12)
        assert "SARIMA" in res.modelo


# ---------------------------------------------------------------------------
# Testes — armax()
# ---------------------------------------------------------------------------

class TestARMAX:
    def test_retorna_tipo(self, serie_ar1):
        rng = np.random.default_rng(11)
        exog = pd.DataFrame({"x": rng.normal(0, 1, len(serie_ar1))}, index=serie_ar1.index)
        res = armax(serie_ar1, p=1, d=0, q=0, exog=exog)
        assert isinstance(res, ModeloResult)

    def test_params_inclui_exog(self, serie_ar1):
        rng = np.random.default_rng(11)
        exog = pd.DataFrame({"x": rng.normal(0, 1, len(serie_ar1))}, index=serie_ar1.index)
        res = armax(serie_ar1, p=1, d=0, q=0, exog=exog)
        assert len(res.params) >= 2


# ---------------------------------------------------------------------------
# Testes — prever()
# ---------------------------------------------------------------------------

class TestPrever:
    def test_retorna_tipo(self, serie_ar1):
        mod = arima(serie_ar1, 1, 0, 1)
        prev = prever(mod, steps=12)
        assert isinstance(prev, PrevisaoResult)

    def test_steps_correto(self, serie_ar1):
        mod = arima(serie_ar1, 1, 0, 1)
        prev = prever(mod, steps=24)
        assert len(prev.valores) == 24

    def test_indices_sao_datas(self, serie_ar1):
        mod = arima(serie_ar1, 1, 0, 1)
        prev = prever(mod, steps=12)
        assert hasattr(prev.valores.index, "year")

    def test_ic_lower_menor_que_upper(self, serie_ar1):
        mod = arima(serie_ar1, 1, 0, 1)
        prev = prever(mod, steps=12)
        if not prev.ic_lower.isna().all():
            assert (prev.ic_lower <= prev.ic_upper).all()


# ---------------------------------------------------------------------------
# Testes — auto_arima()
# ---------------------------------------------------------------------------

class TestAutoArima:
    def test_retorna_tipo(self, serie_ar1):
        res = auto_arima(serie_ar1, max_p=2, max_q=2, max_d=1, stepwise=True)
        assert isinstance(res, ModeloResult)

    def test_modelo_valido(self, serie_ar1):
        res = auto_arima(serie_ar1, max_p=3, max_q=3, max_d=1)
        assert res.aic < 1e6
        assert not np.isnan(res.aic)

    def test_criterio_bic(self, serie_ar1):
        res = auto_arima(serie_ar1, max_p=2, max_q=2, criterio="bic")
        assert isinstance(res, ModeloResult)


# ---------------------------------------------------------------------------
# Testes — criterios()
# ---------------------------------------------------------------------------

class TestCriterios:
    def test_retorna_dataframe(self, serie_ar1):
        df = criterios(serie_ar1, [(0, 1), (1, 0), (1, 1), (2, 0)])
        assert isinstance(df, pd.DataFrame)

    def test_colunas_esperadas(self, serie_ar1):
        df = criterios(serie_ar1, [(1, 0), (0, 1)])
        assert "AIC" in df.columns
        assert "BIC" in df.columns
        assert "LogLik" in df.columns

    def test_indexado_por_p_q(self, serie_ar1):
        df = criterios(serie_ar1, [(1, 0), (0, 1)])
        assert df.index.names == ["p", "q"]


# ---------------------------------------------------------------------------
# Testes — acf_pacf()
# ---------------------------------------------------------------------------

class TestACFPACF:
    def test_retorna_tipo(self, serie_ar1):
        res = acf_pacf(serie_ar1, nlags=20)
        assert isinstance(res, ACFResult)

    def test_comprimentos(self, serie_ar1):
        res = acf_pacf(serie_ar1, nlags=20)
        assert len(res.acf) == res.nlags + 1
        assert len(res.pacf) == res.nlags + 1

    def test_ljung_box_e_dataframe(self, serie_ar1):
        res = acf_pacf(serie_ar1, nlags=20)
        assert isinstance(res.ljung_box, pd.DataFrame)
        assert "pvalue" in res.ljung_box.columns

    def test_acf_lag0_e_1(self, serie_ar1):
        res = acf_pacf(serie_ar1, nlags=10)
        assert abs(res.acf[0] - 1.0) < 1e-10


# ---------------------------------------------------------------------------
# Testes — adf()
# ---------------------------------------------------------------------------

class TestADF:
    def test_retorna_tipo(self, serie_ar1):
        res = adf(serie_ar1)
        assert isinstance(res, RaizResult)

    def test_campos_obrigatorios(self, serie_ar1):
        res = adf(serie_ar1)
        assert isinstance(res.statistic, float)
        assert isinstance(res.pvalue, float)
        assert isinstance(res.rejeita_h0, bool)
        assert isinstance(res.criticos, dict)
        assert "5%" in res.criticos

    def test_metodo_nome(self, serie_ar1):
        res = adf(serie_ar1)
        assert res.metodo == "ADF"

    def test_hipotese_nula(self, serie_ar1):
        res = adf(serie_ar1)
        assert "raiz unitaria" in res.hipotese_nula


# ---------------------------------------------------------------------------
# Testes — pp()
# ---------------------------------------------------------------------------

class TestPP:
    def test_retorna_tipo(self, serie_ar1):
        res = pp(serie_ar1)
        assert isinstance(res, RaizResult)

    def test_metodo_nome(self, serie_ar1):
        res = pp(serie_ar1)
        assert res.metodo == "PP"

    def test_rejeita_h0_e_bool(self, serie_ar1):
        res = pp(serie_ar1)
        assert isinstance(res.rejeita_h0, bool)


# ---------------------------------------------------------------------------
# Testes — kpss()
# ---------------------------------------------------------------------------

class TestKPSS:
    def test_retorna_tipo(self, serie_ar1):
        res = kpss(serie_ar1)
        assert isinstance(res, RaizResult)

    def test_metodo_nome(self, serie_ar1):
        res = kpss(serie_ar1)
        assert res.metodo == "KPSS"

    def test_h0_inversa(self, serie_ar1):
        res = kpss(serie_ar1)
        assert "estacionaria" in res.hipotese_nula


# ---------------------------------------------------------------------------
# Testes — za()
# ---------------------------------------------------------------------------

class TestZA:
    def test_retorna_tipo(self, serie_ar1):
        res = za(serie_ar1)
        assert isinstance(res, RaizResult)

    def test_metodo_nome(self, serie_ar1):
        res = za(serie_ar1)
        assert "Zivot" in res.metodo

    def test_criticos_contem_quebra(self, serie_ar1):
        res = za(serie_ar1)
        assert "quebra_obs" in res.criticos


# ---------------------------------------------------------------------------
# Testes — gph()
# ---------------------------------------------------------------------------

class TestGPH:
    def test_retorna_dict(self, serie_ar1):
        res = gph(serie_ar1)
        assert isinstance(res, dict)

    def test_chaves_presentes(self, serie_ar1):
        res = gph(serie_ar1)
        assert "d" in res
        assert "se" in res
        assert "pvalue" in res
        assert "ic_95" in res

    def test_d_e_float(self, serie_ar1):
        res = gph(serie_ar1)
        assert isinstance(res["d"], float)


# ---------------------------------------------------------------------------
# Testes — arfima()
# ---------------------------------------------------------------------------

class TestARFIMA:
    def test_retorna_tipo(self, serie_ar1):
        res = arfima(serie_ar1, p=1, q=0)
        assert isinstance(res, ModeloResult)

    def test_d_fracionario_presente(self, serie_ar1):
        res = arfima(serie_ar1, p=1, q=0)
        assert "d_fracionario" in res.params.index

    def test_nome_modelo(self, serie_ar1):
        res = arfima(serie_ar1, p=1, q=1)
        assert "ARFIMA" in res.modelo

    def test_d_fixo(self, serie_ar1):
        res = arfima(serie_ar1, p=1, q=0, d=0.3)
        assert abs(res.params["d_fracionario"] - 0.3) < 1e-9
