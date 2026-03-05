"""Testes do módulo SIDRA / IBGE (API IBGE)."""

import pytest
import requests

from data_economist import ibge
from data_economist.fontes.sidra import url


# URL de exemplo da documentação SIDRA (PIMPF por UF)
URL_EXEMPLO = (
    "https://apisidra.ibge.gov.br/values/t/8888/n3/all/v/12606/p/last/c544/129317"
    "/d/v12606%205?formato=json"
)


def test_url_retorna_lista():
    """url(url) devolve uma lista."""
    resultado = url(URL_EXEMPLO)
    assert isinstance(resultado, list)


def test_url_retorna_dicts():
    """Cada elemento da lista é um dicionário."""
    resultado = url(URL_EXEMPLO)
    assert len(resultado) > 0
    for item in resultado:
        assert isinstance(item, dict)


def test_url_primeiro_item_tem_cabecalho():
    """O primeiro elemento costuma ser o cabeçalho (NC, NN, V, etc.)."""
    resultado = url(URL_EXEMPLO)
    primeiro = resultado[0]
    assert "NC" in primeiro or "V" in primeiro or "D1C" in primeiro


def test_url_sem_formato_json():
    """Se a URL não tiver formato=json, a função adiciona."""
    url_sem_formato = (
        "https://apisidra.ibge.gov.br/values/t/8888/n3/all/v/12606/p/last/c544/129317"
    )
    resultado = url(url_sem_formato)
    assert isinstance(resultado, list)
    assert len(resultado) > 0


def test_url_invalida_levanta():
    """URL que retorna 404 ou erro levanta HTTPError."""
    with pytest.raises(requests.HTTPError):
        url("https://apisidra.ibge.gov.br/values/t/99999999")


def test_ibge_url_invalida_levanta():
    """ibge.url(url) com URL inválida levanta HTTPError."""
    with pytest.raises(requests.HTTPError):
        ibge.url("https://apisidra.ibge.gov.br/values/t/99999999")


def test_import_ibge_e_url():
    """from data_economist import ibge; ibge.url() e ibge.get(t,n,v,p,c) existem."""
    assert hasattr(ibge, "url")
    assert hasattr(ibge, "get")
    resultado = ibge.url(URL_EXEMPLO)
    assert isinstance(resultado, list)
    assert len(resultado) > 0


def test_ibge_get_com_parametros_retorna_lista():
    """ibge.get(t, n, v, p, c) monta URL e devolve lista JSON."""
    dados = ibge.get(t=8888, n=(3, "all"), v=12606, p="first", c=(544, 129317))
    assert isinstance(dados, list)
    assert len(dados) > 0
    assert isinstance(dados[0], dict)


def test_ibge_url_aceita_lista_de_urls():
    """ibge.url([url, url]) devolve lista de resultados na mesma ordem (JSON aninhado)."""
    url_sem = (
        "https://apisidra.ibge.gov.br/values/t/8888/n3/all/v/12606/p/last/c544/129317"
    )
    resultados = ibge.url([url_sem, url_sem])
    assert isinstance(resultados, list)
    assert len(resultados) == 2
    assert isinstance(resultados[0], list) and isinstance(resultados[1], list)
    assert len(resultados[0]) > 0 and len(resultados[1]) > 0


def test_ibge_url_sem_formato_json():
    """ibge.url() aceita URL sem formato=json e devolve JSON."""
    url_sem = (
        "https://apisidra.ibge.gov.br/values/t/8888/n3/all/v/12606/p/last/c544/129317"
    )
    resultado = ibge.url(url_sem)
    assert isinstance(resultado, list)
    assert all(isinstance(x, dict) for x in resultado)


def test_ibge_metadados_retorna_dict():
    """ibge.metadados(tabela) devolve um dicionário com metadados."""
    resultado = ibge.metadados(8888)
    assert isinstance(resultado, dict)


def test_ibge_metadados_tem_campos_esperados():
    """ibge.metadados(tabela) inclui id, nome, variaveis, classificacoes."""
    meta = ibge.metadados(8888)
    assert meta.get("id") == 8888
    assert "nome" in meta
    assert "variaveis" in meta
    assert "classificacoes" in meta
    assert "periodicidade" in meta


def test_ibge_metadados_aceita_int_ou_str():
    """ibge.metadados() aceita tabela como int ou str."""
    meta_int = ibge.metadados(8888)
    meta_str = ibge.metadados("8888")
    assert meta_int["id"] == meta_str["id"]
