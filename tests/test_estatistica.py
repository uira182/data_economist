"""
test_estatistica.py — Testes estruturais do módulo estatistica.

Verifica:
- Tipos de retorno corretos
- Atributos presentes nos dataclasses
- Comportamento com dados inválidos (erros esperados)
- Consistência básica dos resultados (pvalue in [0,1], etc.)
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import data_economist.estatistica as est
from data_economist.estatistica import (
    TesteResult,
    ResumoResult,
    DistFitResult,
    CorrelacaoResult,
    TabulacaoResult,
    ContingenciaResult,
    PCAResult,
    FatorialResult,
)


# ---------------------------------------------------------------------------
# Fixtures locais
# ---------------------------------------------------------------------------

@pytest.fixture
def serie_normal():
    rng = np.random.default_rng(42)
    return pd.Series(rng.normal(loc=10.0, scale=2.0, size=100), name="x")


@pytest.fixture
def serie_b():
    rng = np.random.default_rng(7)
    return pd.Series(rng.normal(loc=12.0, scale=2.0, size=100), name="y")


@pytest.fixture
def serie_categorica():
    return pd.Series(["A", "B", "A", "C", "B", "A", "A", "C", "B", "B"] * 10, name="cat")


@pytest.fixture
def df_numerico():
    rng = np.random.default_rng(42)
    n = 80
    x1 = rng.normal(0, 1, n)
    x2 = x1 * 0.7 + rng.normal(0, 0.5, n)
    x3 = rng.normal(0, 1, n)
    return pd.DataFrame({"x1": x1, "x2": x2, "x3": x3})


@pytest.fixture
def grupos_iguais():
    rng = np.random.default_rng(1)
    return (
        pd.Series(rng.normal(5, 1, 40)),
        pd.Series(rng.normal(5, 1, 40)),
        pd.Series(rng.normal(5, 1, 40)),
    )


@pytest.fixture
def grupos_diferentes():
    rng = np.random.default_rng(1)
    return (
        pd.Series(rng.normal(5, 1, 40)),
        pd.Series(rng.normal(10, 1, 40)),
        pd.Series(rng.normal(15, 1, 40)),
    )


# ---------------------------------------------------------------------------
# 3.1 Descritiva
# ---------------------------------------------------------------------------

class TestResumo:
    def test_retorna_tipo_correto(self, serie_normal):
        r = est.resumo(serie_normal)
        assert isinstance(r, ResumoResult)

    def test_atributos_presentes(self, serie_normal):
        r = est.resumo(serie_normal)
        for attr in ("n", "media", "mediana", "minimo", "maximo", "desvio_padrao",
                     "variancia", "assimetria", "curtose", "jarque_bera", "jb_pvalue",
                     "p5", "p25", "p75", "p95", "iqr", "cv"):
            assert hasattr(r, attr), f"Atributo ausente: {attr}"

    def test_n_correto(self, serie_normal):
        r = est.resumo(serie_normal)
        assert r.n == 100

    def test_pvalue_em_range(self, serie_normal):
        r = est.resumo(serie_normal)
        assert 0.0 <= r.jb_pvalue <= 1.0

    def test_erro_serie_vazia(self):
        with pytest.raises(ValueError):
            est.resumo(pd.Series([], dtype=float))

    def test_erro_nao_numerico(self):
        with pytest.raises(ValueError):
            est.resumo(pd.Series(["a", "b", "c"]))


class TestPorGrupo:
    def test_retorna_dict(self, serie_normal):
        grupos = pd.Series(["A"] * 50 + ["B"] * 50)
        r = est.por_grupo(
            pd.DataFrame({"valor": serie_normal, "grupo": grupos}),
            "valor",
            "grupo",
        )
        assert isinstance(r, dict)
        assert set(r.keys()) == {"A", "B"}

    def test_cada_grupo_e_resumo(self, serie_normal):
        grupos = pd.Series(["A"] * 50 + ["B"] * 50)
        r = est.por_grupo(
            pd.DataFrame({"valor": serie_normal, "grupo": grupos}),
            "valor",
            "grupo",
        )
        for v in r.values():
            assert isinstance(v, ResumoResult)


class TestAjustarDistribuicao:
    def test_retorna_tipo_correto(self, serie_normal):
        r = est.ajustar_distribuicao(serie_normal, "normal")
        assert isinstance(r, DistFitResult)

    def test_atributos_aic_bic(self, serie_normal):
        r = est.ajustar_distribuicao(serie_normal, "normal")
        assert hasattr(r, "aic")
        assert hasattr(r, "bic")
        assert r.aic < 0 or r.aic > 0  # apenas verifica que é float finito

    def test_distribuicao_invalida(self, serie_normal):
        with pytest.raises(ValueError):
            est.ajustar_distribuicao(serie_normal, "distribuicao_inexistente")


# ---------------------------------------------------------------------------
# 3.2 Normalidade
# ---------------------------------------------------------------------------

class TestNormalidade:
    def test_ks_retorna_teste_result(self, serie_normal):
        r = est.ks(serie_normal)
        assert isinstance(r, TesteResult)

    def test_lilliefors_retorna_teste_result(self, serie_normal):
        r = est.lilliefors(serie_normal)
        assert isinstance(r, TesteResult)

    def test_anderson_darling_retorna_teste_result(self, serie_normal):
        r = est.anderson_darling(serie_normal)
        assert isinstance(r, TesteResult)

    def test_cramer_von_mises_retorna_teste_result(self, serie_normal):
        r = est.cramer_von_mises(serie_normal)
        assert isinstance(r, TesteResult)

    def test_watson_retorna_teste_result(self, serie_normal):
        r = est.watson(serie_normal)
        assert isinstance(r, TesteResult)

    def test_pvalue_em_range(self, serie_normal):
        for fn in [est.ks, est.lilliefors, est.anderson_darling, est.cramer_von_mises, est.watson]:
            r = fn(serie_normal)
            assert 0.0 <= r.pvalue <= 1.0, f"{fn.__name__}: pvalue={r.pvalue}"

    def test_estatistica_positiva(self, serie_normal):
        for fn in [est.ks, est.lilliefors, est.anderson_darling, est.cramer_von_mises]:
            r = fn(serie_normal)
            assert r.statistic >= 0.0

    def test_rejeita_h0_e_bool(self, serie_normal):
        for fn in [est.ks, est.lilliefors, est.anderson_darling]:
            r = fn(serie_normal)
            assert isinstance(r.rejeita_h0, bool)

    def test_amostra_pequena_levanta_erro(self):
        with pytest.raises(ValueError):
            est.ks(pd.Series([1.0, 2.0]))


# ---------------------------------------------------------------------------
# 3.3 Correlação
# ---------------------------------------------------------------------------

class TestCorrelacao:
    def test_pearson_retorna_tipo(self, serie_normal, serie_b):
        r = est.pearson(serie_normal, serie_b)
        assert isinstance(r, CorrelacaoResult)

    def test_spearman_retorna_tipo(self, serie_normal, serie_b):
        r = est.spearman(serie_normal, serie_b)
        assert isinstance(r, CorrelacaoResult)

    def test_kendall_b_retorna_tipo(self, serie_normal, serie_b):
        r = est.kendall_b(serie_normal, serie_b)
        assert isinstance(r, CorrelacaoResult)

    def test_kendall_a_retorna_tipo(self, serie_normal, serie_b):
        r = est.kendall_a(serie_normal, serie_b)
        assert isinstance(r, CorrelacaoResult)

    def test_coeficiente_em_range(self, serie_normal, serie_b):
        for fn in [est.pearson, est.spearman, est.kendall_b, est.kendall_a]:
            r = fn(serie_normal, serie_b)
            assert -1.0 <= r.coeficiente <= 1.0

    def test_pvalue_em_range(self, serie_normal, serie_b):
        for fn in [est.pearson, est.spearman, est.kendall_b]:
            r = fn(serie_normal, serie_b)
            assert 0.0 <= r.pvalue <= 1.0

    def test_n_correto(self, serie_normal, serie_b):
        r = est.pearson(serie_normal, serie_b)
        assert r.n == 100

    def test_ic_presente_para_pearson(self, serie_normal, serie_b):
        r = est.pearson(serie_normal, serie_b)
        assert r.intervalo_confianca is not None
        assert len(r.intervalo_confianca) == 2

    def test_parcial_retorna_correlacao(self, df_numerico):
        r = est.parcial(df_numerico, "x1", "x2", ["x3"])
        assert isinstance(r, CorrelacaoResult)
        assert -1.0 <= r.coeficiente <= 1.0

    def test_covariancia_retorna_dataframe(self, df_numerico):
        c = est.covariancia(df_numerico)
        assert isinstance(c, pd.DataFrame)
        assert c.shape == (3, 3)

    def test_matriz_correlacao_diagonal_um(self, df_numerico):
        m = est.matriz_correlacao(df_numerico)
        np.testing.assert_allclose(np.diag(m.values), 1.0, atol=1e-10)

    def test_covariancia_simetrica(self, df_numerico):
        c = est.covariancia(df_numerico)
        np.testing.assert_allclose(c.values, c.values.T, atol=1e-10)


# ---------------------------------------------------------------------------
# 3.4 Testes
# ---------------------------------------------------------------------------

class TestHipotese:
    def test_ttest_uma_amostra(self, serie_normal):
        r = est.ttest(serie_normal, valor_ref=10.0)
        assert isinstance(r, TesteResult)
        assert 0.0 <= r.pvalue <= 1.0

    def test_ttest_duas_amostras(self, serie_normal, serie_b):
        r = est.ttest(serie_normal, serie_b)
        assert isinstance(r, TesteResult)
        assert "Welch" in r.metodo

    def test_ttest_pareado(self, serie_normal, serie_b):
        r = est.ttest(serie_normal, serie_b, pareado=True)
        assert "pareado" in r.metodo.lower()

    def test_anova_grupos_iguais_nao_rejeita(self, grupos_iguais):
        r = est.anova(*grupos_iguais)
        assert isinstance(r, TesteResult)
        assert not r.rejeita_h0

    def test_anova_grupos_diferentes_rejeita(self, grupos_diferentes):
        r = est.anova(*grupos_diferentes)
        assert r.rejeita_h0

    def test_wilcoxon_uma_amostra(self, serie_normal):
        r = est.wilcoxon(serie_normal - 10.0)
        assert isinstance(r, TesteResult)

    def test_mann_whitney_retorna_tipo(self, serie_normal, serie_b):
        r = est.mann_whitney(serie_normal, serie_b)
        assert isinstance(r, TesteResult)

    def test_kruskal_wallis_grupos_iguais(self, grupos_iguais):
        r = est.kruskal_wallis(*grupos_iguais)
        assert isinstance(r, TesteResult)
        assert not r.rejeita_h0

    def test_kruskal_wallis_grupos_diferentes(self, grupos_diferentes):
        r = est.kruskal_wallis(*grupos_diferentes)
        assert r.rejeita_h0

    def test_van_der_waerden_retorna_tipo(self, grupos_iguais):
        r = est.van_der_waerden(*grupos_iguais)
        assert isinstance(r, TesteResult)

    def test_teste_f_mesma_variancia(self):
        rng = np.random.default_rng(5)
        x = pd.Series(rng.normal(0, 2, 60))
        y = pd.Series(rng.normal(0, 2, 60))
        r = est.teste_f(x, y)
        assert not r.rejeita_h0

    def test_bartlett_retorna_tipo(self, grupos_iguais):
        r = est.bartlett(*grupos_iguais)
        assert isinstance(r, TesteResult)

    def test_levene_retorna_tipo(self, grupos_iguais):
        r = est.levene(*grupos_iguais)
        assert isinstance(r, TesteResult)

    def test_brown_forsythe_retorna_tipo(self, grupos_iguais):
        r = est.brown_forsythe(*grupos_iguais)
        assert isinstance(r, TesteResult)

    def test_siegel_tukey_retorna_tipo(self, serie_normal, serie_b):
        r = est.siegel_tukey(serie_normal, serie_b)
        assert isinstance(r, TesteResult)

    def test_mediana_chi2_retorna_tipo(self, grupos_iguais):
        r = est.mediana_chi2(*grupos_iguais)
        assert isinstance(r, TesteResult)

    def test_pvalue_sempre_em_range(self, serie_normal, serie_b, grupos_iguais):
        fns_dois = [est.mann_whitney, est.siegel_tukey, est.teste_f]
        for fn in fns_dois:
            r = fn(serie_normal, serie_b)
            assert 0.0 <= r.pvalue <= 1.0, f"{fn.__name__}: {r.pvalue}"


# ---------------------------------------------------------------------------
# 3.5 Contingência
# ---------------------------------------------------------------------------

class TestContingencia:
    def test_tabular_retorna_tipo(self, serie_categorica):
        r = est.tabular(serie_categorica)
        assert isinstance(r, TabulacaoResult)

    def test_tabular_n_correto(self, serie_categorica):
        r = est.tabular(serie_categorica)
        assert r.n == 100

    def test_tabular_ncategorias(self, serie_categorica):
        r = est.tabular(serie_categorica)
        assert r.n_categorias == 3

    def test_tabular_freq_acumulada_100(self, serie_categorica):
        r = est.tabular(serie_categorica)
        ultimo = r.tabela["freq_acumulada_pct"].iloc[-1]
        assert abs(ultimo - 100.0) < 0.1

    def test_cruzar_retorna_tipo(self, serie_categorica):
        x = pd.Series(["A", "B"] * 50)
        y = pd.Series(["X", "Y"] * 50)
        r = est.cruzar(x, y)
        assert isinstance(r, ContingenciaResult)

    def test_cruzar_chi2_positivo(self):
        x = pd.Series(["A", "B"] * 50)
        y = pd.Series(["X", "Y"] * 50)
        r = est.cruzar(x, y)
        assert r.chi2 >= 0.0

    def test_cruzar_phi_tabela_2x2(self):
        x = pd.Series(["A", "A", "B", "B"] * 25)
        y = pd.Series(["X", "Y", "X", "Y"] * 25)
        r = est.cruzar(x, y)
        assert r.phi is not None

    def test_cruzar_v_cramer_range(self):
        x = pd.Series(["A", "B", "C"] * 33)
        y = pd.Series(["X", "Y", "Z"] * 33)
        r = est.cruzar(x, y)
        assert 0.0 <= r.v_cramer <= 1.0

    def test_cruzar_g2_positivo(self):
        x = pd.Series(["A", "B"] * 50)
        y = pd.Series(["X", "Y", "X", "X"] * 25)
        r = est.cruzar(x, y)
        assert r.g2 >= 0.0


# ---------------------------------------------------------------------------
# 3.6 Multivariada
# ---------------------------------------------------------------------------

class TestMultivariada:
    def test_pca_retorna_tipo(self, df_numerico):
        r = est.pca(df_numerico)
        assert isinstance(r, PCAResult)

    def test_pca_n_componentes_default(self, df_numerico):
        r = est.pca(df_numerico)
        assert r.n_componentes == 3

    def test_pca_n_componentes_limitado(self, df_numerico):
        r = est.pca(df_numerico, n_componentes=2)
        assert r.n_componentes == 2
        assert r.cargas.shape == (3, 2)
        assert r.scores.shape[1] == 2

    def test_pca_variancia_acumulada_ordenada(self, df_numerico):
        r = est.pca(df_numerico)
        arr = r.variancia_acumulada.values
        assert (arr[1:] >= arr[:-1]).all()

    def test_pca_variancia_total_1(self, df_numerico):
        r = est.pca(df_numerico)
        assert abs(r.variancia_explicada.sum() - 1.0) < 1e-6

    def test_pca_shape_scores(self, df_numerico):
        r = est.pca(df_numerico, n_componentes=2)
        assert r.scores.shape[0] == len(df_numerico)

    def test_pca_sem_padronizacao(self, df_numerico):
        r = est.pca(df_numerico, padronizar=False)
        assert not r.padronizado

    def test_pca_erro_menos_2_colunas(self):
        with pytest.raises(ValueError):
            est.pca(pd.DataFrame({"x": [1, 2, 3, 4, 5]}))

    def test_fatorial_retorna_tipo(self, df_numerico):
        r = est.fatorial(df_numerico, n_fatores=2)
        assert isinstance(r, FatorialResult)

    def test_fatorial_shape_cargas(self, df_numerico):
        r = est.fatorial(df_numerico, n_fatores=2)
        assert r.cargas.shape == (3, 2)

    def test_fatorial_comunalidades_range(self, df_numerico):
        r = est.fatorial(df_numerico, n_fatores=2)
        assert (r.comunalidades >= 0).all()
        assert (r.comunalidades <= 1.01).all()

    def test_fatorial_unicidades_range(self, df_numerico):
        r = est.fatorial(df_numerico, n_fatores=2)
        assert (r.unicidades >= 0).all()
        assert (r.unicidades <= 1.01).all()

    def test_fatorial_n_fatores_igual_n_variaveis_erro(self, df_numerico):
        with pytest.raises(ValueError):
            est.fatorial(df_numerico, n_fatores=3)
