"""
Módulo estatistica — análise estatística para dados econômicos.

Analise estatistica: descritiva, normalidade, correlacao, testes de hipotese, contingencia, PCA e fatorial.

Submodulos
----------
descritiva   — 3.1: resumo, por_grupo, ajustar_distribuicao
normalidade  — 3.2: ks, lilliefors, anderson_darling, cramer_von_mises, watson
correlacao   — 3.3: pearson, spearman, kendall_b, kendall_a, parcial,
                    covariancia, matriz_correlacao
testes       — 3.4: ttest, anova, wilcoxon, mann_whitney, kruskal_wallis,
                    van_der_waerden, teste_f, bartlett, levene, brown_forsythe,
                    siegel_tukey, mediana_chi2
contingencia — 3.5: tabular, cruzar
multivariada — 3.6: pca, fatorial

Uso
---
    import data_economist as de

    resumo = de.estatistica.resumo(serie)
    r = de.estatistica.pearson(x, y)
    t = de.estatistica.ttest(grupo_a, grupo_b)
    ct = de.estatistica.cruzar(x_cat, y_cat)
    p = de.estatistica.pca(df)
"""

# --- Descritiva ---
from .descritiva import (
    resumo,
    por_grupo,
    ajustar_distribuicao,
    ResumoResult,
    DistFitResult,
)

# --- Normalidade ---
from .normalidade import (
    ks,
    lilliefors,
    anderson_darling,
    cramer_von_mises,
    watson,
)

# --- Correlação ---
from .correlacao import (
    pearson,
    spearman,
    kendall_b,
    kendall_a,
    parcial,
    covariancia,
    matriz_correlacao,
    CorrelacaoResult,
)

# --- Testes ---
from .testes import (
    ttest,
    anova,
    wilcoxon,
    mann_whitney,
    kruskal_wallis,
    van_der_waerden,
    teste_f,
    bartlett,
    levene,
    brown_forsythe,
    siegel_tukey,
    mediana_chi2,
)

# --- Contingência ---
from .contingencia import (
    tabular,
    cruzar,
    TabulacaoResult,
    ContingenciaResult,
)

# --- Multivariada ---
from .multivariada import (
    pca,
    fatorial,
    PCAResult,
    FatorialResult,
)

# --- Resultado compartilhado ---
from ._resultado import TesteResult

__all__ = [
    # descritiva
    "resumo",
    "por_grupo",
    "ajustar_distribuicao",
    "ResumoResult",
    "DistFitResult",
    # normalidade
    "ks",
    "lilliefors",
    "anderson_darling",
    "cramer_von_mises",
    "watson",
    # correlação
    "pearson",
    "spearman",
    "kendall_b",
    "kendall_a",
    "parcial",
    "covariancia",
    "matriz_correlacao",
    "CorrelacaoResult",
    # testes
    "ttest",
    "anova",
    "wilcoxon",
    "mann_whitney",
    "kruskal_wallis",
    "van_der_waerden",
    "teste_f",
    "bartlett",
    "levene",
    "brown_forsythe",
    "siegel_tukey",
    "mediana_chi2",
    # contingência
    "tabular",
    "cruzar",
    "TabulacaoResult",
    "ContingenciaResult",
    # multivariada
    "pca",
    "fatorial",
    "PCAResult",
    "FatorialResult",
    # resultado compartilhado
    "TesteResult",
]
