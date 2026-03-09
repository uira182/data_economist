"""
test_estatistica_mock.py — Validação numérica do módulo estatistica.

Usa séries com propriedades matemáticas conhecidas para verificar a
correção dos cálculos além de tipos e formas.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import data_economist.estatistica as est

RNG = np.random.default_rng(42)


# ---------------------------------------------------------------------------
# Fixtures dedicadas
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def normal_100():
    """N(10, 2), n=100. Deve não rejeitar normalidade."""
    rng = np.random.default_rng(0)
    return pd.Series(rng.normal(10.0, 2.0, 100), name="normal_100")


@pytest.fixture(scope="module")
def nao_normal_100():
    """Chi² com df=1, n=100. Deve rejeitar normalidade."""
    rng = np.random.default_rng(0)
    return pd.Series(rng.chisquare(df=1, size=100), name="nao_normal_100")


@pytest.fixture(scope="module")
def linear_x():
    """x = 1..50."""
    return pd.Series(np.arange(1, 51, dtype=float), name="x")


@pytest.fixture(scope="module")
def linear_y():
    """y = 2*x + 1. Correlação de Pearson = 1.0 com linear_x."""
    x = np.arange(1, 51, dtype=float)
    return pd.Series(2.0 * x + 1.0, name="y")


@pytest.fixture(scope="module")
def grupo_a():
    rng = np.random.default_rng(10)
    return pd.Series(rng.normal(5.0, 1.0, 500))


@pytest.fixture(scope="module")
def grupo_b_igual():
    rng = np.random.default_rng(11)
    return pd.Series(rng.normal(5.0, 1.0, 500))


@pytest.fixture(scope="module")
def grupo_b_diferente():
    rng = np.random.default_rng(12)
    return pd.Series(rng.normal(15.0, 1.0, 500))


@pytest.fixture(scope="module")
def df_correlacionado():
    """x1 e x2 com correlação esperada ~0.95."""
    rng = np.random.default_rng(99)
    n = 100
    x1 = rng.normal(0, 1, n)
    x2 = x1 * 0.95 + rng.normal(0, 0.31, n)
    x3 = rng.normal(0, 1, n)
    return pd.DataFrame({"x1": x1, "x2": x2, "x3": x3})


# ---------------------------------------------------------------------------
# 3.1 Descritiva — correção numérica
# ---------------------------------------------------------------------------

class TestResumoNumerica:
    def test_media_proxima_do_esperado(self, normal_100):
        r = est.resumo(normal_100)
        assert abs(r.media - 10.0) < 0.6

    def test_std_proxima_do_esperado(self, normal_100):
        r = est.resumo(normal_100)
        assert abs(r.desvio_padrao - 2.0) < 0.5

    def test_min_menor_que_media(self, normal_100):
        r = est.resumo(normal_100)
        assert r.minimo < r.media

    def test_max_maior_que_media(self, normal_100):
        r = est.resumo(normal_100)
        assert r.maximo > r.media

    def test_p25_menor_que_p75(self, normal_100):
        r = est.resumo(normal_100)
        assert r.p25 < r.p75

    def test_iqr_igual_p75_menos_p25(self, normal_100):
        r = est.resumo(normal_100)
        assert abs(r.iqr - (r.p75 - r.p25)) < 1e-8

    def test_cv_positivo(self, normal_100):
        r = est.resumo(normal_100)
        assert r.cv > 0.0

    def test_normal_jb_nao_rejeita(self, normal_100):
        r = est.resumo(normal_100)
        assert r.jb_pvalue > 0.01

    def test_n_nan_excluidos(self):
        s = pd.Series([1.0, 2.0, np.nan, 4.0, 5.0])
        r = est.resumo(s)
        assert r.n == 4


# ---------------------------------------------------------------------------
# 3.2 Normalidade — correção numérica
# ---------------------------------------------------------------------------

class TestNormalidadeNumerica:
    def test_ks_normal_nao_rejeita(self, normal_100):
        r = est.ks(normal_100)
        assert not r.rejeita_h0

    def test_lilliefors_normal_nao_rejeita(self, normal_100):
        r = est.lilliefors(normal_100)
        assert not r.rejeita_h0

    def test_anderson_darling_normal_nao_rejeita(self, normal_100):
        r = est.anderson_darling(normal_100)
        assert not r.rejeita_h0

    def test_cramer_von_mises_normal_nao_rejeita(self, normal_100):
        r = est.cramer_von_mises(normal_100)
        assert not r.rejeita_h0

    def test_watson_normal_nao_rejeita(self, normal_100):
        r = est.watson(normal_100)
        assert not r.rejeita_h0

    def test_ks_nao_normal_rejeita(self, nao_normal_100):
        r = est.ks(nao_normal_100)
        assert r.rejeita_h0

    def test_lilliefors_nao_normal_rejeita(self, nao_normal_100):
        r = est.lilliefors(nao_normal_100)
        assert r.rejeita_h0

    def test_anderson_nao_normal_rejeita(self, nao_normal_100):
        r = est.anderson_darling(nao_normal_100)
        assert r.rejeita_h0


# ---------------------------------------------------------------------------
# 3.3 Correlação — correção numérica
# ---------------------------------------------------------------------------

class TestCorrelacaoNumerica:
    def test_pearson_correlacao_perfeita(self, linear_x, linear_y):
        r = est.pearson(linear_x, linear_y)
        assert abs(r.coeficiente - 1.0) < 1e-6

    def test_pearson_nao_correlacionados(self):
        rng = np.random.default_rng(20)
        x = pd.Series(rng.normal(0, 1, 100))
        y = pd.Series(rng.normal(0, 1, 100))
        r = est.pearson(x, y)
        assert abs(r.coeficiente) < 0.3

    def test_spearman_monotona(self, linear_x):
        y = linear_x ** 2
        r = est.spearman(linear_x, y)
        assert abs(r.coeficiente - 1.0) < 1e-6

    def test_pearson_ic_contem_coeficiente(self, linear_x, linear_y):
        r = est.pearson(linear_x, linear_y)
        assert r.intervalo_confianca[0] <= r.coeficiente <= r.intervalo_confianca[1]

    def test_matriz_correlacao_x1_x2_alta(self, df_correlacionado):
        m = est.matriz_correlacao(df_correlacionado)
        assert m.loc["x1", "x2"] > 0.85

    def test_covariancia_simetrica(self, df_correlacionado):
        c = est.covariancia(df_correlacionado)
        np.testing.assert_allclose(c.values, c.values.T, atol=1e-10)

    def test_kendall_b_perfeito(self, linear_x, linear_y):
        r = est.kendall_b(linear_x, linear_y)
        assert abs(r.coeficiente - 1.0) < 1e-6

    def test_parcial_remove_confusao(self, df_correlacionado):
        r = est.parcial(df_correlacionado, "x1", "x2", ["x3"])
        assert abs(r.coeficiente) > 0.7


# ---------------------------------------------------------------------------
# 3.4 Testes — correção numérica
# ---------------------------------------------------------------------------

class TestHipoteseNumerica:
    def test_ttest_media_conhecida_nao_rejeita(self, normal_100):
        r = est.ttest(normal_100, valor_ref=10.0)
        assert not r.rejeita_h0

    def test_ttest_media_errada_rejeita(self, normal_100):
        r = est.ttest(normal_100, valor_ref=0.0)
        assert r.rejeita_h0

    def test_ttest_grupos_iguais_nao_rejeita(self, grupo_a, grupo_b_igual):
        r = est.ttest(grupo_a, grupo_b_igual, alpha=0.01)
        assert not r.rejeita_h0

    def test_ttest_grupos_diferentes_rejeita(self, grupo_a, grupo_b_diferente):
        r = est.ttest(grupo_a, grupo_b_diferente)
        assert r.rejeita_h0

    def test_anova_grupos_iguais_nao_rejeita(self, grupo_a, grupo_b_igual):
        rng = np.random.default_rng(2)
        g3 = pd.Series(rng.normal(5.0, 1.0, 500))
        r = est.anova(grupo_a, grupo_b_igual, g3, alpha=0.01)
        assert not r.rejeita_h0

    def test_anova_grupos_diferentes_rejeita(self, grupo_a, grupo_b_diferente):
        r = est.anova(grupo_a, grupo_b_diferente)
        assert r.rejeita_h0

    def test_mann_whitney_iguais_nao_rejeita(self, grupo_a, grupo_b_igual):
        r = est.mann_whitney(grupo_a, grupo_b_igual, alpha=0.01)
        assert not r.rejeita_h0

    def test_mann_whitney_diferentes_rejeita(self, grupo_a, grupo_b_diferente):
        r = est.mann_whitney(grupo_a, grupo_b_diferente)
        assert r.rejeita_h0

    def test_kruskal_diferentes_rejeita(self, grupo_a, grupo_b_diferente):
        r = est.kruskal_wallis(grupo_a, grupo_b_diferente)
        assert r.rejeita_h0

    def test_bartlett_variancia_igual_nao_rejeita(self, grupo_a, grupo_b_igual):
        r = est.bartlett(grupo_a, grupo_b_igual)
        assert not r.rejeita_h0

    def test_levene_variancia_diferente_rejeita(self):
        rng = np.random.default_rng(30)
        x = pd.Series(rng.normal(0, 1, 100))
        y = pd.Series(rng.normal(0, 10, 100))
        r = est.levene(x, y)
        assert r.rejeita_h0

    def test_brown_forsythe_variancia_diferente_rejeita(self):
        rng = np.random.default_rng(31)
        x = pd.Series(rng.normal(0, 1, 100))
        y = pd.Series(rng.normal(0, 10, 100))
        r = est.brown_forsythe(x, y)
        assert r.rejeita_h0

    def test_siegel_tukey_dispersao_igual_nao_rejeita(self, grupo_a, grupo_b_igual):
        r = est.siegel_tukey(grupo_a, grupo_b_igual)
        assert not r.rejeita_h0

    def test_van_der_waerden_grupos_diferentes(self, grupo_a, grupo_b_diferente):
        r = est.van_der_waerden(grupo_a, grupo_b_diferente)
        assert r.rejeita_h0


# ---------------------------------------------------------------------------
# 3.5 Contingência — correção numérica
# ---------------------------------------------------------------------------

class TestContingenciaNumerica:
    def test_tabular_frequencia_correta(self):
        s = pd.Series(["A"] * 60 + ["B"] * 40, name="cat")
        r = est.tabular(s)
        assert r.tabela.iloc[0]["freq_absoluta"] == 60
        rel = r.tabela.iloc[0]["freq_relativa_pct"]
        assert abs(rel - 60.0) < 0.01

    def test_cruzar_independente_nao_rejeita(self):
        rng = np.random.default_rng(50)
        x = pd.Series(rng.choice(["A", "B"], size=200))
        y = pd.Series(rng.choice(["X", "Y"], size=200))
        r = est.cruzar(x, y)
        assert not r.rejeita_independencia

    def test_cruzar_dependente_rejeita(self):
        x = pd.Series(["A"] * 100 + ["B"] * 100)
        y = pd.Series(["X"] * 100 + ["Y"] * 100)
        r = est.cruzar(x, y)
        assert r.rejeita_independencia

    def test_v_cramer_associacao_perfeita(self):
        x = pd.Series(["A"] * 50 + ["B"] * 50)
        y = pd.Series(["X"] * 50 + ["Y"] * 50)
        r = est.cruzar(x, y)
        assert r.v_cramer > 0.9

    def test_g2_proxima_chi2_para_n_grande(self):
        rng = np.random.default_rng(55)
        x = pd.Series(rng.choice(["A", "B", "C"], size=500))
        y = pd.Series(rng.choice(["X", "Y"], size=500))
        r = est.cruzar(x, y)
        assert abs(r.chi2 - r.g2) / max(r.chi2, 1e-9) < 0.5


# ---------------------------------------------------------------------------
# 3.6 Multivariada — correção numérica
# ---------------------------------------------------------------------------

class TestMultivariadaNumerica:
    def test_pca_primeira_cp_maxima_variancia(self, df_correlacionado):
        r = est.pca(df_correlacionado)
        v = r.variancia_explicada.values
        assert v[0] >= v[1]

    def test_pca_variancia_acumulada_100(self, df_correlacionado):
        r = est.pca(df_correlacionado)
        assert abs(r.variancia_acumulada.iloc[-1] - 1.0) < 1e-6

    def test_pca_autovalores_positivos(self, df_correlacionado):
        r = est.pca(df_correlacionado)
        assert (r.autovalores.values > 0).all()

    def test_pca_dados_correlacionados_1cp_domina(self, df_correlacionado):
        r = est.pca(df_correlacionado, n_componentes=3)
        assert r.variancia_explicada.iloc[0] > 0.5

    def test_fatorial_comunalidade_alta_x1_x2(self, df_correlacionado):
        r = est.fatorial(df_correlacionado, n_fatores=2)
        assert r.comunalidades["x1"] > 0.3
        assert r.comunalidades["x2"] > 0.3

    def test_fatorial_unicidade_mais_comunalidade_aproxima_1(self, df_correlacionado):
        r = est.fatorial(df_correlacionado, n_fatores=2)
        soma = r.unicidades + r.comunalidades
        np.testing.assert_allclose(soma.values, 1.0, atol=1e-6)
