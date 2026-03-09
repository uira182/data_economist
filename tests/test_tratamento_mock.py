"""
Testes de correção numérica do módulo tratamento usando séries mock.

Diferença em relação a test_tratamento.py
------------------------------------------
test_tratamento.py verifica estrutura: tipos, formas, atributos presentes.
Este arquivo verifica correção: os valores calculados estão matematicamente
certos, dentro das tolerâncias definidas no MockSeries.expected.

Cada teste usa uma série cuja resposta correta é conhecida a priori.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from data_economist.tratamento import (
    bk,
    cf,
    ciclo,
    ets,
    forecast,
    holt,
    holt_winters,
    hp,
    para_frequencia,
    serie_branca,
    ses,
    suavizado,
    tendencia,
    whitening,
)


# ---------------------------------------------------------------------------
# Utilitários locais
# ---------------------------------------------------------------------------

def correlacao(a: pd.Series, b: pd.Series) -> float:
    """Correlação de Pearson entre duas séries alinhadas pelo índice."""
    combinado = pd.DataFrame({"a": a, "b": b}).dropna()
    return float(combinado["a"].corr(combinado["b"]))


def max_abs(s: pd.Series) -> float:
    return float(s.dropna().abs().max())


def media(s: pd.Series) -> float:
    return float(s.dropna().mean())


# ===========================================================================
# Filtro HP — validação numérica
# ===========================================================================

class TestHPCorreto:

    def test_ciclo_quase_zero_em_tendencia_linear(self, mock_tendencia_linear):
        """
        Sobre uma tendência linear pura, o ciclo HP deve ser praticamente zero.
        O HP extrai exatamente a tendência de um polinômio de baixo grau.
        """
        r = hp(mock_tendencia_linear.series)
        limite = mock_tendencia_linear.expected["hp_ciclo_max_abs"]
        assert max_abs(ciclo(r)) < limite, (
            f"Ciclo HP máximo: {max_abs(ciclo(r)):.4f} — esperado < {limite}"
        )

    def test_tendencia_segue_serie_linear(self, mock_tendencia_linear):
        """Tendência HP deve ser altamente correlacionada com a tendência verdadeira."""
        r = hp(mock_tendencia_linear.series)
        corr = correlacao(tendencia(r), mock_tendencia_linear.series)
        minimo = mock_tendencia_linear.expected["hp_tendencia_corr_min"]
        assert corr >= minimo, f"Correlação tendência HP vs original: {corr:.4f} — mínimo {minimo}"

    def test_ciclo_zero_exato_em_constante(self, mock_constante):
        """Sobre série constante, o ciclo HP deve ser zero absoluto."""
        r = hp(mock_constante.series)
        limite = mock_constante.expected["hp_ciclo_max_abs"]
        assert max_abs(ciclo(r)) < limite

    def test_tendencia_valor_constante(self, mock_constante):
        """Tendência HP de série constante deve ser igual à constante."""
        r = hp(mock_constante.series)
        valor_esperado = mock_constante.expected["hp_tendencia_valor"]
        desvio = abs(media(tendencia(r)) - valor_esperado)
        assert desvio < 1e-6, f"Média da tendência: {media(tendencia(r)):.6f} — esperado {valor_esperado}"

    def test_tendencia_sazonal_captura_nivel(self, mock_sazonal_pura):
        """Em série sazonal pura, a tendência HP deve estar próxima do nível central."""
        r = hp(mock_sazonal_pura.series, lamb=1_000_000)  # lambda alto isola nível
        media_tendencia = media(tendencia(r))
        nivel_esperado = mock_sazonal_pura.expected["hp_tendencia_media_esperada"]
        desvio_max = mock_sazonal_pura.expected["hp_tendencia_desvio_max"]
        assert abs(media_tendencia - nivel_esperado) < desvio_max, (
            f"Média da tendência: {media_tendencia:.2f} — esperado próximo de {nivel_esperado}"
        )

    def test_ciclo_completo_componentes_somam_original(self, mock_serie_completa):
        """tendencia + ciclo deve reconstituir a série original."""
        r = hp(mock_serie_completa.series)
        reconstruida = tendencia(r) + ciclo(r)
        desvio = (mock_serie_completa.series - reconstruida).dropna().abs().max()
        assert desvio < 1e-8, f"Desvio máximo na reconstrução: {desvio:.2e}"


# ===========================================================================
# Filtros BK e CF — validação numérica
# ===========================================================================

class TestBKCorreto:

    def test_ciclo_correlaciona_com_sazonal_pura(self, mock_sazonal_pura):
        """
        BK sobre série sazonal pura com [6,18] deve extrair o ciclo com
        alta correlação com a série original (que é quase só ciclo).
        """
        r = bk(mock_sazonal_pura.series, low=6, high=18, K=6)
        # O ciclo extraído deve ter sinal próximo à série original (dropando as bordas)
        serie_interna = mock_sazonal_pura.series.reindex(ciclo(r).index)
        corr = correlacao(ciclo(r), serie_interna)
        minimo = mock_sazonal_pura.expected["bk_ciclo_corr_min"]
        assert corr >= minimo, f"Correlação BK ciclo vs original: {corr:.4f} — mínimo {minimo}"

    def test_ciclo_bk_tem_media_zero(self, mock_sazonal_pura):
        """O filtro BK remove a tendência: a média do ciclo deve ser ≈ 0."""
        r = bk(mock_sazonal_pura.series, low=6, high=18, K=6)
        assert abs(media(ciclo(r))) < 1.0


class TestCFCorreto:

    def test_ciclo_cf_correlaciona_sazonal(self, mock_sazonal_pura):
        """CF com os mesmos parâmetros de BK deve também isolar a sazonalidade."""
        r = cf(mock_sazonal_pura.series, low=6, high=18)
        corr = abs(correlacao(ciclo(r), mock_sazonal_pura.series))
        assert corr >= 0.80, f"Correlação CF ciclo vs original: {corr:.4f}"

    def test_ciclo_cf_mesmo_tamanho_serie(self, mock_sazonal_pura):
        """CF de amostra completa preserva o tamanho da série."""
        r = cf(mock_sazonal_pura.series, symmetric=False)
        assert len(ciclo(r)) == len(mock_sazonal_pura.series)


# ===========================================================================
# Suavização Exponencial Simples (SES) — validação numérica
# ===========================================================================

class TestSESCorreto:

    def test_suavizado_igual_constante(self, mock_constante):
        """SES sobre série constante deve resultar em suavizado ≈ constante."""
        r = ses(mock_constante.series)
        desvio = mock_constante.expected["ses_suavizado_max_desvio"]
        assert max_abs(suavizado(r) - mock_constante.series) < desvio

    def test_suavizado_dentro_range_tendencia(self, mock_tendencia_linear):
        """SES sobre tendência linear: suavizado deve estar entre min e max da série."""
        r = ses(mock_tendencia_linear.series)
        s = suavizado(r).dropna()
        minimo = float(mock_tendencia_linear.series.min())
        maximo = float(mock_tendencia_linear.series.max())
        assert float(s.min()) >= minimo - 5
        assert float(s.max()) <= maximo + 5

    def test_forecast_continua_range_plausivel(self, mock_tendencia_linear):
        """Previsão de 12 passos deve estar em range plausível da série."""
        r = ses(mock_tendencia_linear.series)
        prev = forecast(r, steps=12)
        assert len(prev) == 12
        # SES não captura tendência, então a previsão deve ser próxima da última observação
        ultima = float(mock_tendencia_linear.series.iloc[-1])
        assert float(prev.mean()) < ultima * 2  # verificação básica de sanidade


# ===========================================================================
# Holt — validação numérica
# ===========================================================================

class TestHoltCorreto:

    def test_suavizado_constante(self, mock_constante):
        """Holt sobre constante deve produzir suavizado ≈ constante."""
        r = holt(mock_constante.series)
        desvio = mock_constante.expected["holt_suavizado_max_desvio"]
        assert max_abs(suavizado(r) - mock_constante.series) < desvio

    def test_holt_captura_tendencia(self, mock_tendencia_linear):
        """Holt deve capturar a tendência: suavizado deve correlacionar com original."""
        r = holt(mock_tendencia_linear.series)
        corr = correlacao(suavizado(r), mock_tendencia_linear.series)
        assert corr >= 0.99, f"Correlação Holt vs tendência linear: {corr:.4f}"

    def test_forecast_holt_extrapolacao(self, mock_tendencia_linear):
        """Holt com tendência linear deve extrapolar para além do último valor."""
        r = holt(mock_tendencia_linear.series)
        prev = forecast(r, steps=6)
        ultimo = float(mock_tendencia_linear.series.iloc[-1])
        # Com tendência crescente, a previsão deve superar o último valor
        assert float(prev.iloc[-1]) > ultimo


# ===========================================================================
# Holt-Winters — validação numérica
# ===========================================================================

class TestHoltWintersCorreto:

    def test_aic_finito_serie_completa(self, mock_serie_completa):
        """Holt-Winters deve convergir e ter AIC finito."""
        r = holt_winters(mock_serie_completa.series, seasonal="add")
        assert mock_serie_completa.expected["hw_aic_finito"]
        assert r.aic is not None
        assert np.isfinite(r.aic)

    def test_gamma_positivo_serie_sazonal(self, mock_sazonal_pura):
        """Com sazonalidade forte, gamma deve ser estimado positivo."""
        r = holt_winters(mock_sazonal_pura.series, seasonal="add")
        assert r.gamma is not None
        assert r.gamma > 0

    def test_suavizado_cobre_range_serie_completa(self, mock_serie_completa):
        """Suavizado deve estar dentro do range da série original."""
        r = holt_winters(mock_serie_completa.series, seasonal="add")
        s = suavizado(r)
        original = mock_serie_completa.series
        margem = float(original.std()) * 3
        assert float(s.min()) >= float(original.min()) - margem
        assert float(s.max()) <= float(original.max()) + margem

    def test_forecast_hw_doze_passos(self, mock_serie_completa):
        """Previsão de 12 meses deve ser gerada com datas futuras."""
        r = holt_winters(mock_serie_completa.series, seasonal="add")
        prev = forecast(r, steps=12)
        assert len(prev) == 12
        assert prev.index.min() > mock_serie_completa.series.index.max()


# ===========================================================================
# ETS — validação numérica
# ===========================================================================

class TestETSCorreto:

    def test_ets_aic_menor_que_ses_em_sazonal(self, mock_sazonal_pura):
        """ETS auto deve selecionar modelo com sazonalidade, com AIC menor que SES."""
        r_ets = ets(mock_sazonal_pura.series)
        r_ses = ses(mock_sazonal_pura.series)
        assert r_ets.aic < r_ses.aic, (
            f"AIC ETS ({r_ets.aic:.1f}) deveria ser < AIC SES ({r_ses.aic:.1f})"
        )

    def test_ets_aic_finito(self, mock_serie_completa):
        r = ets(mock_serie_completa.series)
        assert np.isfinite(r.aic)

    def test_ets_suavizado_mesmo_tamanho(self, mock_serie_completa):
        r = ets(mock_serie_completa.series)
        assert len(suavizado(r)) == len(mock_serie_completa.series)


# ===========================================================================
# Whitening — validação numérica
# ===========================================================================

class TestWhiteningCorreto:

    def test_coeficiente_ar1_recuperado(self, mock_ar1):
        """
        Whitening com lags=1 sobre AR(1) verdadeiro deve recuperar o
        coeficiente phi ≈ 0.8 dentro da tolerância definida na fixture.
        """
        r = whitening(mock_ar1.series, lags=1)
        phi_verdadeiro = mock_ar1.expected["whitening_coef_ar1_valor"]
        tol = mock_ar1.expected["whitening_coef_ar1_tol"]
        coef = float(r.coeficientes.iloc[0])
        assert abs(coef - phi_verdadeiro) < tol, (
            f"Coeficiente AR(1) estimado: {coef:.3f} — "
            f"verdadeiro: {phi_verdadeiro} ± {tol}"
        )

    def test_residuos_menor_variancia_que_original(self, mock_ar1):
        """Os resíduos do AR(1) devem ter variância menor que a série original."""
        r = whitening(mock_ar1.series, lags=1)
        std_original = float(mock_ar1.series.std())
        std_branca = float(serie_branca(r).std())
        assert std_branca < std_original, (
            f"Std branca ({std_branca:.4f}) deve ser < Std original ({std_original:.4f})"
        )

    def test_residuos_menor_std_serie_completa(self, mock_serie_completa):
        """
        Whitening de série autocorrelacionada deve reduzir o desvio padrão
        (proporção std_branca / std_original deve ser < 0.9).
        """
        r = whitening(mock_serie_completa.series)
        ratio = float(serie_branca(r).std()) / float(mock_serie_completa.series.std())
        limite = mock_serie_completa.expected["whitening_std_ratio_max"]
        assert ratio < limite, (
            f"Ratio std_branca/std_original: {ratio:.3f} — esperado < {limite}"
        )

    def test_residuos_constante_sao_zero(self, mock_constante):
        """Whitening de série constante deve produzir resíduos ≈ zero."""
        r = whitening(mock_constante.series, lags=1)
        assert max_abs(serie_branca(r)) < 1e-6


# ===========================================================================
# Conversão de frequência — validação numérica
# ===========================================================================

class TestFrequenciaCorreta:

    def test_mensal_para_trimestral_conserva_media(self, mock_tendencia_linear):
        """
        Agregação mensal→trimestral por média deve conservar o nível central.
        A média do resultado deve estar dentro do range da série original.
        """
        s = mock_tendencia_linear.series
        r = para_frequencia(s, freq="QE", metodo="mean")
        assert float(r.min()) >= float(s.min()) - 1
        assert float(r.max()) <= float(s.max()) + 1

    def test_mensal_para_trimestral_sum_maior_que_mean(self, mock_tendencia_linear):
        """
        Agregação por soma deve produzir valores ~3x maiores que por média
        (pois há ~3 meses por trimestre).
        """
        s = mock_tendencia_linear.series
        r_mean = para_frequencia(s, freq="QE", metodo="mean")
        r_sum = para_frequencia(s, freq="QE", metodo="sum")
        ratio = float(r_sum.mean()) / float(r_mean.mean())
        assert 2.5 < ratio < 3.5, f"Ratio sum/mean: {ratio:.2f} — esperado ≈ 3"

    def test_constante_preservada_em_qualquer_metodo(self, mock_constante):
        """Para série constante, qualquer método de agregação deve retornar a constante."""
        s = mock_constante.series
        valor = mock_constante.expected["freq_valor_esperado"]
        for metodo in ("mean", "sum", "first", "last", "max", "min"):
            # sum tem valor ~3x por ter 3 meses no trimestre
            if metodo == "sum":
                continue
            r = para_frequencia(s, freq="QE", metodo=metodo)
            desvio = abs(float(r.mean()) - valor)
            assert desvio < 1e-6, f"Método '{metodo}': desvio {desvio:.2e}"

    def test_interpolacao_linear_dentro_range(self, mock_tendencia_linear):
        """
        Interpolação linear de mensal para diário deve manter os valores
        dentro do range da série original (sem extrapolação nos extremos).
        """
        s = mock_tendencia_linear.series
        r = para_frequencia(s, freq="D", metodo="linear")
        assert float(r.min()) >= float(s.min()) - 0.5
        assert float(r.max()) <= float(s.max()) + 0.5

    def test_interpolacao_ffill_mantém_valor_ate_proximo(self, mock_constante):
        """
        Forward-fill de série constante mensal para diária deve retornar
        sempre o mesmo valor.
        """
        s = mock_constante.series
        r = para_frequencia(s, freq="D", metodo="ffill")
        valor = mock_constante.expected["freq_valor_esperado"]
        assert max_abs(r - valor) < 1e-6

    def test_diario_para_mensal_reduce_tamanho(self, mock_serie_diaria):
        """Conversão diária→mensal deve reduzir drasticamente o número de pontos."""
        r = para_frequencia(mock_serie_diaria.series, freq="ME", metodo="mean")
        assert len(r) < len(mock_serie_diaria.series) / 10

    def test_diario_para_mensal_valores_no_range(self, mock_serie_diaria):
        """Médias mensais devem estar dentro do range da série diária."""
        s = mock_serie_diaria.series
        r = para_frequencia(s, freq="ME", metodo="mean")
        assert float(r.min()) >= float(s.min()) - 1
        assert float(r.max()) <= float(s.max()) + 1


# ===========================================================================
# Fluxo completo — validação ponta a ponta
# ===========================================================================

class TestFluxoCompleto:

    def test_hp_depois_whitening_residuos_pequenos(self, mock_sazonal_pura):
        """
        Ciclo extraído pelo HP (que representa a sazonalidade) pode ser
        branqueado pelo whitening. Os resíduos devem ter variância menor.
        """
        r_hp = hp(mock_sazonal_pura.series, lamb=1_000_000)
        r_w = whitening(ciclo(r_hp))
        std_ciclo = float(ciclo(r_hp).std())
        std_branca = float(serie_branca(r_w).std())
        assert std_branca < std_ciclo

    def test_converter_e_filtrar_consistente(self, mock_serie_diaria):
        """
        Converter série diária para mensal e aplicar HP deve produzir
        tendência correlacionada com a tendência verdadeira da série.
        """
        mensal = para_frequencia(mock_serie_diaria.series, freq="ME", metodo="mean")
        r_hp = hp(mensal)
        # Tendência deve ser altamente correlacionada com a série mensal
        corr = correlacao(tendencia(r_hp), mensal)
        assert corr >= 0.99

    def test_holt_winters_previsao_e_comparacao_ses(self, mock_serie_completa):
        """
        Para série com sazonalidade clara, HW deve ter AIC menor que SES.
        """
        r_hw = holt_winters(mock_serie_completa.series, seasonal="add")
        r_ses = ses(mock_serie_completa.series)
        assert r_hw.aic < r_ses.aic
