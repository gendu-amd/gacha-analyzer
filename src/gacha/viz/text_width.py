"""终端表格列宽：正确处理 CJK 等 East Asian 双宽字符（D25）。"""

from __future__ import annotations

import unicodedata


def display_width(text: str) -> int:
    """字符串在等宽终端中的显示宽度（CJK 全角字符计 2）。"""
    w = 0
    for ch in text:
        if unicodedata.east_asian_width(ch) in ("F", "W"):
            w += 2
        else:
            w += 1
    return w


def ljust_display(text: str, width: int) -> str:
    """左对齐到指定显示宽度。"""
    pad = width - display_width(text)
    return text + " " * max(0, pad)


def rjust_display(text: str, width: int) -> str:
    """右对齐到指定显示宽度。"""
    pad = width - display_width(text)
    return " " * max(0, pad) + text


def format_row(cells: list[str], widths: list[int], aligns: list[str] | None = None) -> str:
    """按列宽与对齐方式拼接一行。"""
    aligns = aligns or ["left"] * len(cells)
    parts = []
    for cell, w, align in zip(cells, widths, aligns):
        if align == "right":
            parts.append(rjust_display(cell, w))
        else:
            parts.append(ljust_display(cell, w))
    return "".join(parts)
