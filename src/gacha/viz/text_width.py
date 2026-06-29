"""终端表格列宽：用标准 ``wcwidth`` 库计算显示宽度（D25）。

不再手写 ``unicodedata.east_asian_width`` 逐字符判定——``wcwidth`` 是 POSIX
``wcwidth(3)`` 的成熟移植，除 CJK 全角外还正确处理零宽/组合字符与控制符。
"""

from __future__ import annotations

from wcwidth import wcswidth, wcwidth as _wcwidth


def display_width(text: str) -> int:
    """字符串在等宽终端中的显示宽度（CJK 全角字符计 2，零宽字符计 0）。"""
    w = wcswidth(text)
    if w >= 0:
        return w
    # wcswidth 遇到控制字符会返回 -1；按字符累加并把不可打印字符当作 0 宽。
    return sum(max(_wcwidth(ch), 0) for ch in text)


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
