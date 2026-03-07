"""
Teste completo: inicialização (venv + x13binary), série histórica aleatória
mensal 2000-01 a 2026-03, ajuste sazonal X-13, resultado final [data, valor, valor_dessaz].
"""

from pathlib import Path
import sys

# Garantir que o pacote está no path (quando se corre a partir do repo)
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np
import pandas as pd

# ---- Etapa 1: Inicialização (venv + x13binary) ----
print("=" * 60)
print("Etapa 1: Inicialização (venv + x13binary)")
print("=" * 60)
try:
    from data_economist import x13
    root = Path(__file__).resolve().parents[1]
    venv_path = x13.init(project_root=root)
    print(f"  OK. Venv em: {venv_path}")
except Exception as e:
    print(f"  Erro na inicialização: {e}")
    sys.exit(1)

# ---- Etapa 2: Gerar série histórica mensal (2000-01 a 2026-03) ----
print()
print("=" * 60)
print("Etapa 2: Gerar série histórica mensal (2000-01 a 2026-03)")
print("=" * 60)
idx = pd.date_range("2000-01-01", "2026-03-01", freq="ME")
np.random.seed(42)
# Tendência + sazonalidade + ruído (evita erro "differencing annihilated" no X-13)
tendencia = np.linspace(100, 180, len(idx))
sazonal = 15 * np.sin(2 * np.pi * np.arange(len(idx)) / 12)
ruido = np.random.normal(0, 5, len(idx))
valores = tendencia + sazonal + ruido
serie = pd.Series(valores, index=idx, name="valor")
print(f"  OK. Série com {len(serie)} meses.")
print(f"  Primeiros 3: {serie.head(3).tolist()}")
print(f"  Últimos 3:   {serie.tail(3).tolist()}")

# ---- Etapa 3: Ajuste sazonal X-13 (dessaz) ----
print()
print("=" * 60)
print("Etapa 3: Executando ajuste sazonal X-13 (dessaz)")
print("=" * 60)
try:
    modelo = x13.seas(serie, title="serie_historica_teste")
    print("  OK. Modelo X-13 concluído.")
except Exception as e:
    print(f"  Erro no ajuste: {e}")
    sys.exit(1)

# ---- Etapa 4: Montar resultado [data, valor, valor_dessaz] ----
print()
print("=" * 60)
print("Etapa 4: Montar resultado (data, valor, valor_dessaz)")
print("=" * 60)
original = x13.original(modelo)
dessaz = x13.final(modelo)
resultado = pd.DataFrame({
    "data": original.index,
    "valor": original.values,
    "valor_dessaz": dessaz.values,
})
print(f"  OK. DataFrame com {len(resultado)} linhas e 3 colunas.")

# ---- Etapa 5: Resultado final (amostra) ----
print()
print("=" * 60)
print("Etapa 5: Resultado final (data, valor, valor_dessaz)")
print("=" * 60)
print(f"Total de registos: {len(resultado)}")
print()
print("Primeiros 10:")
print(resultado.head(10).to_string(index=False))
print()
print("Últimos 10:")
print(resultado.tail(10).to_string(index=False))
print()
print("Concluído. DataFrame completo em variável 'resultado'.")
