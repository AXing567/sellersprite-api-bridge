"""
通用网页表格解析工具
------------------------------------------------
卖家精灵各业务页面（选品、选词、选市场、竞品反查）均为服务端渲染的 HTML 表格，
本模块提供「表头驱动」的稳健解析能力：先读取 thead 的中文列名，再按列名取值，
即使官网调整列顺序也不会解析错位。
"""
import re
from typing import List, Dict, Optional, Tuple, Any

from bs4 import BeautifulSoup


# ---------------- 数值清洗 ----------------

def to_number(text: Optional[str]) -> Optional[float]:
    """把 '12,345'、'$1,234.5'、'37.31%'、'1.2K' 等文本转成数值"""
    if text is None:
        return None
    s = str(text).strip()
    if not s:
        return None
    # 去掉货币符号、千分位、空白
    s = s.replace(",", "").replace("$", "").replace("¥", "").replace("€", "").replace("£", "").replace("￥", "")
    s = s.replace("\u00a0", "").strip()

    # 处理 K / M / W 等缩写
    mult = 1.0
    if s.endswith("K") or s.endswith("k"):
        mult, s = 1_000.0, s[:-1]
    elif s.endswith("M") or s.endswith("m"):
        mult, s = 1_000_000.0, s[:-1]
    elif s.endswith("W") or s.endswith("w"):
        mult, s = 10_000.0, s[:-1]

    is_pct = s.endswith("%")
    if is_pct:
        s = s[:-1]

    m = re.search(r"-?\d+(?:\.\d+)?", s)
    if not m:
        return None
    try:
        val = float(m.group(0)) * mult
        return val
    except ValueError:
        return None


def to_int(text: Optional[str]) -> Optional[int]:
    v = to_number(text)
    return int(v) if v is not None else None


def to_ratio(text: Optional[str]) -> Optional[float]:
    """百分比文本转 0~1 的小数"""
    v = to_number(text)
    if v is None:
        return None
    return round(v / 100.0, 4)


# ---------------- 表格提取 ----------------

def extract_tables(html: str) -> List[Dict[str, Any]]:
    """提取页面所有表格，返回 [{classes, headers, rows, nodes}]"""
    soup = BeautifulSoup(html, "html.parser")
    result = []
    for table in soup.find_all("table"):
        classes = table.get("class") or []
        headers = _read_headers(table)
        rows, nodes = _read_rows(table, with_nodes=True)
        if headers or rows:
            result.append({
                "classes": classes,
                "headers": headers,
                "rows": rows,
                "nodes": nodes,
            })
    return result


_TR_RE = re.compile(r"<tr\b[^>]*>(.*?)</tr>", re.S | re.I)
_TD_RE = re.compile(r"<td\b([^>]*)>(.*?)</td>", re.S | re.I)


def extract_rows_loose(html: str, min_cells: int = 8) -> Tuple[List[str], List[List[str]], List[list]]:
    """
    容错行提取器。

    卖家精灵部分页面（如「选产品」）返回的 HTML 结构不完整——`<tr>` 没有正确嵌套在
    `<tbody>` 内，BeautifulSoup 会把它们挂到 `<body>` 或 `<div>` 上，
    导致常规 tbody 遍历只能拿到 1 行。本函数用正则直接扫全文所有 `<tr>`，
    再逐个 td 片段交给 BeautifulSoup 建 DOM，从而拿到完整商品行。

    返回 (headers, rows, nodes)
    """
    soup = BeautifulSoup(html, "html.parser")

    # 表头：取第一个包含表头单元格的 thead
    headers: List[str] = []
    for thead in soup.find_all("thead"):
        cells = thead.find_all(["th", "td"])
        if len(cells) >= 3:
            headers = [re.sub(r"\s+", " ", c.get_text(" ", strip=True)) for c in cells]
            break

    rows: List[List[str]] = []
    nodes: List[list] = []

    for m in _TR_RE.finditer(html):
        tr_html = m.group(0)
        cells = _TD_RE.findall(tr_html)
        if len(cells) < min_cells:
            continue

        texts: List[str] = []
        node_list = []
        for attrs, inner in cells:
            frag = f"<td{attrs}>{inner}</td>"
            td = BeautifulSoup(frag, "html.parser").find("td")
            node_list.append(td)
            txt = re.sub(r"\s+", " ", td.get_text(" ", strip=True))
            texts.append(txt)

        rows.append(texts)
        nodes.append(node_list)

    return headers, rows, nodes


def _read_headers(table) -> List[str]:
    thead = table.find("thead")
    if not thead:
        return []
    cells = thead.find_all(["th", "td"])
    headers = []
    for c in cells:
        txt = c.get_text(" ", strip=True)
        txt = re.sub(r"\s+", " ", txt)
        headers.append(txt)
    return headers


def _read_rows(table, with_nodes: bool = False):
    body = table.find("tbody") or table
    rows = []
    nodes = []
    for tr in body.find_all("tr", recursive=False) or body.find_all("tr"):
        tds = tr.find_all("td", recursive=False)
        if not tds:
            continue
        cells = []
        for td in tds:
            txt = td.get_text(" ", strip=True)
            txt = re.sub(r"\s+", " ", txt)
            cells.append(txt)
        rows.append(cells)
        if with_nodes:
            nodes.append(tds)
    if with_nodes:
        return rows, nodes
    return rows


def pick_table(html: str, prefer_class: Optional[str] = None, min_rows: int = 1) -> Optional[Dict[str, Any]]:
    """挑选最像数据表的那个表格"""
    tables = extract_tables(html)
    if not tables:
        return None
    if prefer_class:
        for t in tables:
            if prefer_class in (t["classes"] or []) and len(t["rows"]) >= min_rows:
                return t
    tables.sort(key=lambda t: len(t["rows"]), reverse=True)
    for t in tables:
        if len(t["rows"]) >= min_rows and len(t["headers"]) >= 3:
            return t
    return tables[0]


# ---------------- 表头映射 ----------------

def build_header_index(headers: List[str]) -> Dict[str, int]:
    """规范化表头，构建 列名->索引 映射（同时保留原始与简化名）"""
    idx = {}
    for i, h in enumerate(headers):
        idx[h] = i
        # 简化：去掉中文说明后缀
        simple = re.split(r"[（(]", h)[0].strip()
        if simple and simple not in idx:
            idx[simple] = i
    return idx


def find_col(headers: List[str], *aliases: str) -> Optional[int]:
    """按别名模糊匹配列索引。aliases 按优先级排列。"""
    for alias in aliases:
        for i, h in enumerate(headers):
            if alias in h:
                return i
    return None


def cell(row: List[str], i: Optional[int]) -> Optional[str]:
    if i is None or i < 0 or i >= len(row):
        return None
    return row[i]


def read_tiered_number(row: List[str], i: Optional[int], level: int = 0) -> Optional[float]:
    """
    卖家精灵的复合单元格常含多行数值（如 '2,568 6,300' 表示主营/全部），
    本函数按层级取第 level 个数值。
    """
    raw = cell(row, i)
    if not raw:
        return None
    parts = [p for p in re.split(r"[\s\n]+", raw) if p.strip()]
    if len(parts) > level:
        return to_number(parts[level])
    return to_number(raw)
