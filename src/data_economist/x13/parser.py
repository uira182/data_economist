"""
Lê os ficheiros de saída do X-13 (.udg, .html/.out) e preenche estruturas de resultado.
"""

from __future__ import annotations

import re
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

import pandas as pd


def _extract_tables_from_html(html_path: Path) -> list[list[list[str]]]:
    """Extrai todas as tabelas do HTML como lista de linhas (cada linha = lista de células)."""
    if not html_path.is_file():
        return []
    text = html_path.read_text(encoding="utf-8", errors="ignore")

    class Parser(HTMLParser):
        def __init__(self):
            super().__init__()
            self.tables: list[list[list[str]]] = []
            self.rows: list[list[str]] = []
            self.cells: list[str] = []
            self.in_cell = False
        def handle_starttag(self, tag, attrs):
            if tag == "table":
                self.rows = []
            elif tag in ("td", "th"):
                self.in_cell = True
                self.cells.append("")
        def handle_endtag(self, tag):
            if tag in ("td", "th"):
                self.in_cell = False
            elif tag == "tr":
                if self.cells:
                    self.rows.append(self.cells)
                self.cells = []
            elif tag == "table" and self.rows:
                self.tables.append(self.rows)
        def handle_data(self, data):
            if self.in_cell and self.cells:
                self.cells[-1] += data.strip()

    p = Parser()
    p.feed(text)
    if p.cells:
        p.rows.append(p.cells)
    if p.rows and (not p.tables or p.rows != p.tables[-1]):
        p.tables.append(p.rows)
    return p.tables


def _parse_series_table(rows: list[list[str]], expected_len: int) -> list[float] | None:
    """
    De uma tabela com cabeçalho (ex.: '', 'Jan', 'Feb', ...) e linhas (ano, v1..v12, TOTAL),
    extrai os valores mensais; ignora linha AVGE e TOTAL. Aceita último ano incompleto.
    Devolve lista de float ou None.
    """
    if len(rows) < 2:
        return None
    vals: list[float] = []
    for row in rows[1:]:
        if not row or len(row) < 2:
            continue
        first = row[0].strip().upper()
        if first == "AVGE" or first == "":
            continue
        if not first.isdigit():
            continue
        for c in row[1:13]:
            if len(vals) >= expected_len:
                break
            s = c.strip()
            if not s:
                continue
            # Aceitar vírgula como separador decimal (ex.: "21,94")
            s_clean = s.replace(",", "")
            try:
                v = float(s_clean)
            except ValueError:
                try:
                    v = float(s.replace(",", "."))
                except ValueError:
                    continue  # ignora célula inválida em vez de falhar a tabela
            vals.append(v)
    if len(vals) < expected_len:
        return None
    return vals[:expected_len]


def _extract_table_at_position(text: str, start: int) -> list[list[str]] | None:
    """Extrai uma única tabela a partir da posição start (onde começa <table)."""
    end = text.find("</table>", start)
    if end < 0:
        return None
    fragment = text[start : end + 8]
    from html.parser import HTMLParser

    class P(HTMLParser):
        def __init__(self):
            super().__init__()
            self.rows: list[list[str]] = []
            self.cells: list[str] = []
            self.in_cell = False
        def handle_starttag(self, tag, attrs):
            if tag in ("td", "th"):
                self.in_cell = True
                self.cells.append("")
        def handle_endtag(self, tag):
            if tag in ("td", "th"):
                self.in_cell = False
            elif tag == "tr" and self.cells:
                self.rows.append(self.cells)
                self.cells = []
        def handle_data(self, data):
            if self.in_cell and self.cells:
                self.cells[-1] += data.strip()
    p = P()
    p.feed(fragment)
    if p.cells:
        p.rows.append(p.cells)
    return p.rows if p.rows else None


def _parse_html_components(
    html_path: Path,
    index: pd.DatetimeIndex,
) -> tuple[pd.Series | None, pd.Series | None, pd.Series | None]:
    """
    Lê io.html, identifica tabelas S 11 (ajustada), S 12 (tendência), S 13 (irregular)
    pelo texto/caption da tabela, e devolve (final, trend, irregular).
    """
    if not html_path.is_file():
        return None, None, None
    text = html_path.read_text(encoding="utf-8", errors="ignore")
    n = len(index)
    table_starts = [m.start() for m in re.finditer(r"<table", text, re.IGNORECASE)]
    final_vals: list[float] | None = None
    trend_vals: list[float] | None = None
    irregular_vals: list[float] | None = None
    # Fallback: primeira tabela com n valores cujo texto contenha "seasonally adjusted" (sem S 11)
    fallback_final: list[float] | None = None

    for i, start in enumerate(table_starts):
        tab = _extract_table_at_position(text, start)
        if tab is None:
            continue
        window_start = max(0, start - 400)
        window_end = min(len(text), start + 1200)
        after = text[window_start:window_end]
        after_clean = re.sub(r"<[^>]+>", " ", after).upper()
        vals = _parse_series_table(tab, n)
        if vals is None:
            continue
        if "S 11" in after_clean or "S11" in after_clean or (
            "FINAL SEASONALLY ADJUSTED" in after_clean and "FORECAST" not in after_clean
        ):
            final_vals = vals
        elif "D11" in after_clean:
            # Algumas versões do X-13 usam D11 para a série ajustada
            if final_vals is None:
                final_vals = vals
        elif "S 12" in after_clean or "S12" in after_clean or "FINAL TREND COMPONENT" in after_clean:
            trend_vals = vals
        elif "S 13" in after_clean or "S13" in after_clean or "FINAL IRREGULAR" in after_clean:
            irregular_vals = vals
        elif final_vals is None and "SEASONALLY ADJUSTED" in after_clean and "FORECAST" not in after_clean:
            fallback_final = vals

    if final_vals is None and fallback_final is not None:
        final_vals = fallback_final

    final = pd.Series(final_vals, index=index, dtype=float) if final_vals else None
    trend = pd.Series(trend_vals, index=index, dtype=float) if trend_vals else None
    irregular = pd.Series(irregular_vals, index=index, dtype=float) if irregular_vals else None
    return final, trend, irregular


def _diagnose_html(html_path: Path, n: int) -> list[str]:
    """Gera linhas de diagnóstico sobre o conteúdo do HTML quando o parsing falha."""
    lines: list[str] = []
    if not html_path.is_file():
        return ["HTML não encontrado: " + str(html_path)]
    text = html_path.read_text(encoding="utf-8", errors="ignore")
    table_starts = [m.start() for m in re.finditer(r"<table", text, re.IGNORECASE)]
    lines.append(f"HTML: {len(table_starts)} tabelas, esperadas {n} valores.")
    for i, start in enumerate(table_starts):
        tab = _extract_table_at_position(text, start)
        if tab is None:
            continue
        vals = _parse_series_table(tab, n)
        if vals is not None:
            window_start = max(0, start - 300)
            window_end = min(len(text), start + 600)
            snippet = re.sub(r"<[^>]+>", " ", text[window_start:window_end]).replace("\n", " ")[:200]
            snippet = " ".join(snippet.split())
            lines.append(f"  Tabela {i+1}: {len(vals)} valores. Texto: ...{snippet}...")
    return lines


def parse_udg(udg_path: Path | str) -> dict[str, Any]:
    """
    Interpreta o ficheiro .udg (diagnósticos) como dicionário key: value.
    Valores numéricos são convertidos a float quando possível.
    """
    path = Path(udg_path)
    if not path.is_file():
        return {}
    text = path.read_text(encoding="utf-8", errors="ignore")
    out: dict[str, Any] = {}
    for line in text.splitlines():
        line = line.strip()
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        key = key.strip()
        val = val.strip()
        if not key:
            continue
        # Tentar numérico
        try:
            if "E" in val.upper() or "." in val:
                out[key] = float(val)
            else:
                out[key] = int(val)
        except ValueError:
            out[key] = val
    return out


def _parse_series_from_html(html_path: Path, index: pd.DatetimeIndex) -> pd.Series | None:
    """
    Tenta extrair uma série temporal de uma tabela no HTML.
    Espera tabelas com ano na primeira coluna e meses nas seguintes (12 cols).
    Devolve None se não encontrar formato adequado.
    """
    if not html_path.is_file():
        return None
    text = html_path.read_text(encoding="utf-8", errors="ignore")
    # Procurar blocos de números que possam ser ano + 12 meses
    # Padrão: números separados por espaço ou </td><td>
    numbers = re.findall(r">\s*([-]?\d+\.?\d*[Ee]?[-+]?\d*)\s*<", text)
    if len(numbers) < len(index):
        return None
    try:
        vals = [float(x) for x in numbers[: len(index)]]
        return pd.Series(vals, index=index, dtype=float)
    except (ValueError, TypeError):
        return None


def _read_seats_txt(path: Path, index: pd.DatetimeIndex) -> pd.Series | None:
    """
    Lê um arquivo de texto gerado pelo X-13 via seats{save=(s11 s12 s13)}.

    Formato esperado: uma observação por linha, com valores numéricos separados
    por espaço. Pode ter cabeçalho, linhas em branco ou comentários (ignorados).
    Suporta dois formatos:
      - "YYYY.MM  valor"  (ex: "2020.01  0.21345")
      - apenas o valor numérico por linha

    Retorna pd.Series alinhada com index, ou None se leitura falhar.
    """
    if not path.is_file():
        return None
    try:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError:
        return None

    vals: list[float] = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        # Ignorar linhas de cabeçalho/texto (não numéricas)
        parts = line.split()
        # Tentar o último token como valor (cobre "YYYY.MM  valor" e só "valor")
        for token in reversed(parts):
            try:
                v = float(token)
                vals.append(v)
                break
            except ValueError:
                continue

    if len(vals) < len(index):
        return None
    return pd.Series(vals[: len(index)], index=index, dtype=float)


def parse_output(
    work_dir: Path | str,
    base_name: str,
    original_series: pd.Series,
) -> dict[str, Any]:
    """
    Lê os ficheiros de saída do X-13 no work_dir (base_name.out, base_name.udg, etc.)
    e devolve um dicionário com:
      - original: série original
      - final: série dessazonalizada (ou cópia da original se não disponível)
      - trend: tendência (ou None)
      - irregular: irregular (ou None)
      - udg: dict de diagnósticos
      - messages: lista de mensagens/avisos

    Estratégia de leitura (ordem de preferência):
    1. Arquivos de texto salvos pelo seats{save=(s11 s12 s13)} — precisão total.
    2. Tabelas do HTML — fallback, mas pode truncar casas decimais para séries
       de pequena magnitude (ex.: IPCA variação mensal em %).
    """
    work_dir = Path(work_dir)
    base = base_name.replace(".spc", "").replace(".udg", "").replace(".html", "")

    result: dict[str, Any] = {
        "original": original_series,
        "final": None,
        "trend": None,
        "irregular": None,
        "udg": {},
        "messages": [],
    }

    # .udg
    udg_path = work_dir / f"{base}.udg"
    result["udg"] = parse_udg(udg_path)

    # Índice temporal (mesmo que a série original)
    index = original_series.index
    if not isinstance(index, pd.DatetimeIndex):
        index = pd.DatetimeIndex(pd.period_range(start="2000-01", periods=len(original_series), freq="ME"))

    # --- Prioridade 1: arquivos de texto gerados por seats{save=(s11 s12 s13)} ---
    final_txt = _read_seats_txt(work_dir / f"{base}.s11", index)
    trend_txt = _read_seats_txt(work_dir / f"{base}.s12", index)
    irregular_txt = _read_seats_txt(work_dir / f"{base}.s13", index)

    if final_txt is not None:
        result["final"] = final_txt
        result["trend"] = trend_txt      # pode ser None se s12 não existir
        result["irregular"] = irregular_txt
        return result

    # --- Prioridade 2: tabelas HTML ---
    html_path = work_dir / f"{base}.html"
    final_s, trend_s, irregular_s = _parse_html_components(html_path, index)
    if final_s is not None:
        result["final"] = final_s
        result["trend"] = trend_s
        result["irregular"] = irregular_s
    else:
        result["final"] = original_series.copy()
        path_msg = str(html_path.resolve()) if html_path.is_file() else f"(ficheiro não encontrado: {html_path})"
        result["messages"].append(
            "Componentes (final/trend/irregular) não extraídos do output; final=original. "
            "Use model.udg para diagnósticos. HTML: " + path_msg
        )
        for line in _diagnose_html(html_path, len(index)):
            result["messages"].append(line)

    return result
