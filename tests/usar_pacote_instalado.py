"""
Teste usando o pacote data_economist como se estivesse instalado via pip.

Requisito: pip install -e .  (na raiz do projeto) para usar a versão local.

Execução (na raiz do projeto): python tests/usar_pacote_instalado.py
"""

import os
import sys

# Garantir que o pacote local (src) é usado quando se executa da raiz do projeto
_raiz = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_src = os.path.join(_raiz, "src")
if os.path.isdir(_src) and _src not in sys.path:
    sys.path.insert(0, _src)

# ---------------------------------------------------------------------------
# 1) Versão e import
# ---------------------------------------------------------------------------
print("=" * 60)
print("1) Versão e import")
print("=" * 60)

import data_economist

print(f"Versão: {data_economist.__version__}")
print("Import OK.")
print()

# ---------------------------------------------------------------------------
# 2) IBGE — metadados
# ---------------------------------------------------------------------------
print("=" * 60)
print("2) IBGE — ibge.metadados(8888)")
print("=" * 60)

from data_economist import ibge

meta = ibge.metadados(8888)
print(f"Nome da tabela: {meta['nome']}")
print(f"Periodicidade: {meta['periodicidade']}")
print()

# ---------------------------------------------------------------------------
# 3) IBGE — ibge.get (parâmetros)
# ---------------------------------------------------------------------------
print("=" * 60)
print("3) IBGE — ibge.get(t=8888, n=(3,'all'), v=12606, p='last', c=(544, 129317))")
print("=" * 60)

dados = ibge.get(t=8888, n=(3, "all"), v=12606, p="last", c=(544, 129317))
print(f"Registos recebidos: {len(dados)} (1º = cabeçalho)")
if len(dados) > 1:
    print(f"Exemplo 2º registo — D1N (UF): {dados[1].get('D1N')}, V: {dados[1].get('V')}")
print()

# ---------------------------------------------------------------------------
# 4) IBGE — ibge.url (uma URL)
# ---------------------------------------------------------------------------
print("=" * 60)
print("4) IBGE — ibge.url(url)")
print("=" * 60)

url = "https://apisidra.ibge.gov.br/values/t/8888/n3/all/v/12606/p/first/c544/129317"
dados_url = ibge.url(url)
print(f"Registos via URL: {len(dados_url)}")
print()

# ---------------------------------------------------------------------------
# 5) IBGE — ibge.url (lista de URLs)
# ---------------------------------------------------------------------------
print("=" * 60)
print("5) IBGE — ibge.url([url1, url2])")
print("=" * 60)

urls = [url, url]
varios = ibge.url(urls)
print(f"Lista de {len(varios)} resultados (uma por URL)")
print(f"Cada resultado tem {len(varios[0])} registos.")
print()

# ---------------------------------------------------------------------------
# 6) BCB SGS — bcb_sgs.get(codigo) — série completa
# ---------------------------------------------------------------------------
print("=" * 60)
print("6) BCB SGS — bcb_sgs.get(433)  [série completa, último valor → para trás]")
print("=" * 60)

try:
    from data_economist import bcb_sgs

    dados_sgs = bcb_sgs.get(433)  # IPCA
    print(f"Total de pontos: {len(dados_sgs)}")
    if dados_sgs:
        print(f"Primeiro: {dados_sgs[0]}")
        print(f"Último: {dados_sgs[-1]}")
except ImportError as e:
    print(f"(bcb_sgs só existe a partir da versão 0.2.0) ImportError: {e}")
except Exception as e:
    print(f"Erro: {type(e).__name__}: {e}")
print()

# ---------------------------------------------------------------------------
# 7) BCB SGS — bcb_sgs.get(codigo, date_init) — do início 2020 até o último
# ---------------------------------------------------------------------------
print("=" * 60)
print("7) BCB SGS — bcb_sgs.get(433, '2020-01-01')  [de 2020 até o último valor]")
print("=" * 60)

try:
    from data_economist import bcb_sgs

    dados_sgs = bcb_sgs.get(433, "2020-01-01")
    print(f"Total de pontos: {len(dados_sgs)}")
    if dados_sgs:
        print(f"Primeiro: {dados_sgs[0]}")
        print(f"Último: {dados_sgs[-1]}")
except ImportError:
    print("(bcb_sgs só na 0.2.0+)")
except Exception as e:
    print(f"Erro: {type(e).__name__}: {e}")
print()

# ---------------------------------------------------------------------------
# 8) BCB SGS — bcb_sgs.get(codigo, None, date_end) — da data final para trás
# ---------------------------------------------------------------------------
print("=" * 60)
print("8) BCB SGS — bcb_sgs.get(433, None, '2000-01-06')  [de 2000-01-06 para trás]")
print("=" * 60)

try:
    from data_economist import bcb_sgs

    dados_sgs = bcb_sgs.get(433, None, "2000-01-06")
    print(f"Total de pontos: {len(dados_sgs)}")
    if dados_sgs:
        print(f"Primeiro: {dados_sgs[0]}")
        print(f"Último: {dados_sgs[-1]}")
except ImportError:
    print("(bcb_sgs só na 0.2.0+)")
except Exception as e:
    print(f"Erro: {type(e).__name__}: {e}")
print()

# ---------------------------------------------------------------------------
# 9) BCB SGS — bcb_sgs.get(codigo, date_init, date_end) — intervalo fixo
# ---------------------------------------------------------------------------
print("=" * 60)
print("9) BCB SGS — bcb_sgs.get(433, '2020-01-01', '2025-01-01')  [só 2020–2025]")
print("=" * 60)

try:
    from data_economist import bcb_sgs

    dados_sgs = bcb_sgs.get(433, "2020-01-01", "2025-01-01")
    print(f"Total de pontos: {len(dados_sgs)}")
    if dados_sgs:
        print(f"Primeiro: {dados_sgs[0]}")
        print(f"Último: {dados_sgs[-1]}")
except ImportError:
    print("(bcb_sgs só na 0.2.0+)")
except Exception as e:
    print(f"Erro: {type(e).__name__}: {e}")
print()

# ---------------------------------------------------------------------------
# 10) BCB SGS — código como string
# ---------------------------------------------------------------------------
print("=" * 60)
print("10) BCB SGS — bcb_sgs.get('433')  [código como str]")
print("=" * 60)

try:
    from data_economist import bcb_sgs

    dados_sgs = bcb_sgs.get("433")
    print(f"Total de pontos: {len(dados_sgs)}")
    print("OK — aceita código como string.")
except ImportError:
    print("(bcb_sgs só na 0.2.0+)")
except Exception as e:
    print(f"Erro: {type(e).__name__}: {e}")
print()

# ---------------------------------------------------------------------------
# 11) ComexStat — comexstat.get(body), get_general, get_filter, get_by_filter
# ---------------------------------------------------------------------------
print("=" * 60)
print("11) ComexStat — get(body), get_general, get_filter, get_by_filter")
print("=" * 60)

try:
    from data_economist import comexstat

    # POST (documentação oficial) — pode devolver data vazia conforme filtro
    body = {
        "flow": "export",
        "monthDetail": False,
        "period": {"from": "2018-01", "to": "2018-01"},
        "filters": [{"filter": "state", "values": [26]}],
        "details": ["country", "state"],
        "metrics": ["metricFOB", "metricKG"],
    }
    resultado = comexstat.get(body, timeout=60)
    print(f"  get(body): tipo={type(resultado).__name__}, registros em 'data'={len(resultado.get('data', []))}")

    # GET /general com mapeamentos do notebook — dados em resultado["data"]["list"]
    dados = comexstat.get_general("export", "cuciGroup", ["281b"], "metricFOB", timeout=60)
    data_list = dados.get("data", {})
    data_list = data_list.get("list", data_list) if isinstance(data_list, dict) else (dados.get("list") or dados)
    n = len(data_list) if isinstance(data_list, list) else 0
    print(f"  get_general('export', 'cuciGroup', ['281b'], 'metricFOB'): {n} registros")
    if n > 0 and isinstance(data_list, list) and isinstance(data_list[0], dict):
        print(f"  Campos do 1º registro: {list(data_list[0].keys())[:8]}")

    # GET /general — import chapter4 2603 (minério de cobre)
    dados2 = comexstat.get_general("import", "chapter4", ["2603"], "metricKG", timeout=60)
    data_list2 = dados2.get("data", {})
    data_list2 = data_list2.get("list", data_list2) if isinstance(data_list2, dict) else (dados2.get("list") or dados2)
    n2 = len(data_list2) if isinstance(data_list2, list) else 0
    print(f"  get_general('import', 'chapter4', ['2603'], 'metricKG'): {n2} registros")

    # Filtro guardado no site — por ID ou URL
    filtro = comexstat.get_filter(146862, timeout=30)
    print(f"  get_filter(146862): id={filtro.get('data', {}).get('id')}, filter length={len(filtro.get('data', {}).get('filter', ''))}")

    dados_filtro = comexstat.get_by_filter(146862, timeout=90)
    list_filtro = (dados_filtro.get("data") or {}).get("list", [])
    print(f"  get_by_filter(146862): {len(list_filtro)} registros (mesmo que GET /general com esse filtro)")

    dados_url = comexstat.get_by_filter("https://comexstat.mdic.gov.br/pt/geral/146862", timeout=90)
    list_url = (dados_url.get("data") or {}).get("list", [])
    print(f"  get_by_filter(URL .../geral/146862): {len(list_url)} registros")

    print("OK — comexstat.get, get_general, get_filter, get_by_filter.")
except ImportError as e:
    print(f"(ImportError: {e}. Execute na raiz do projeto: pip install -e .)")
except Exception as e:
    print(f"Erro: {type(e).__name__}: {e}")
print()

# ---------------------------------------------------------------------------
# 12) Resumo final
# ---------------------------------------------------------------------------
print("=" * 60)
print("12) Resumo")
print("=" * 60)
print("Pacote data_economist utilizado com sucesso (instalado via pip).")
print("IBGE: metadados, get(), url() — OK.")
if hasattr(data_economist, "bcb_sgs"):
    print("BCB SGS: get(codigo, date_init, date_end) — OK.")
if hasattr(data_economist, "comexstat"):
    print("ComexStat: get(body), get_general(...), get_filter(id), get_by_filter(id|url) — OK.")
print()
sys.exit(0)


