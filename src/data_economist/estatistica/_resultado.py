"""
Objetos de resultado compartilhados pelo módulo estatistica.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class TesteResult:
    """
    Resultado genérico de um teste de hipótese.

    Atributos
    ---------
    statistic : float
        Valor da estatística do teste.
    pvalue : float
        p-valor do teste.
    metodo : str
        Nome do teste realizado.
    hipotese_nula : str
        Descrição da hipótese nula (H0).
    conclusao : str
        Conclusão automática com base no nível de significância.
    rejeita_h0 : bool
        True se H0 é rejeitada ao nível alpha.
    alpha : float
        Nível de significância usado (padrão 0.05).
    params : dict
        Parâmetros adicionais do teste (graus de liberdade, etc.).
    """

    statistic: float
    pvalue: float
    metodo: str
    hipotese_nula: str
    conclusao: str
    rejeita_h0: bool
    alpha: float = 0.05
    params: dict = field(default_factory=dict)

    def __str__(self) -> str:
        linhas = [
            f"Teste: {self.metodo}",
            f"H0: {self.hipotese_nula}",
            f"Estatística: {self.statistic:.4f}",
            f"p-valor: {self.pvalue:.4f}",
            f"Nível alpha: {self.alpha}",
            f"Conclusão: {self.conclusao}",
        ]
        if self.params:
            for k, v in self.params.items():
                if isinstance(v, float):
                    linhas.append(f"  {k}: {v:.4f}")
                else:
                    linhas.append(f"  {k}: {v}")
        return "\n".join(linhas)


def _concluir(pvalue: float, alpha: float, h0: str) -> tuple[str, bool]:
    """Gera conclusão e flag rejeita_h0 com base no p-valor."""
    rejeita = bool(pvalue < alpha)
    if rejeita:
        conclusao = f"Rejeita H0 (p={pvalue:.4f} < alpha={alpha}): {h0} não sustentada."
    else:
        conclusao = f"Não rejeita H0 (p={pvalue:.4f} >= alpha={alpha}): {h0} não descartada."
    return conclusao, rejeita
