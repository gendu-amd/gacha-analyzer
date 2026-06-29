"""Unified design tokens for matplotlib static plots and Plotly HTML reports.

Professional data-tool aesthetic (paimon.moe / SRS clarity inspired, not game UI).
"""

from __future__ import annotations

import os
import tempfile

# Ensure matplotlib cache is writable before any mpl import elsewhere.
os.environ.setdefault("MPLCONFIGDIR", os.path.join(tempfile.gettempdir(), "gacha-mpl"))

# ---- Palette ----
BLUE = "#3D6FE5"
BLUE_FILL = "#9DBBF6"
BLUE_LIGHT = "#E8EEFB"
GREEN = "#1F9E78"
GREEN_FILL = "#A0E0C8"
AMBER = "#E8A317"
RED = "#E4572E"
PURPLE = "#8E5BD6"
INK = "#1F2937"
MUTED = "#6B7280"
BORDER = "#D0D7DE"
GRID = "#E6EAF0"
BG_PAGE = "#F4F6FA"
BG_CARD = "#FBFCFE"
BG_ACCENT = "#F8FAFF"
WATERMARK = "#B6BECC"

# Per-game series colors (cross-game charts)
GAME_COLORS = {
    "genshin": BLUE,
    "hsr": GREEN,
    "zzz": PURPLE,
}
GAME_COLOR_LIST = [BLUE, GREEN, PURPLE, AMBER, RED]

# Heatmap — single source of truth shared by matplotlib (PNG) and Plotly (HTML).
# Low cost = calm blue, mid = amber, high = red. Same identity across both renderers.
HEATMAP_ANCHORS = (BLUE_LIGHT, AMBER, RED)
HEATMAP_SCALE_PLOTLY = [[0.0, BLUE_LIGHT], [0.5, AMBER], [1.0, RED]]
# Above this fraction of the max value, cells are dark enough to need white text.
HEATMAP_WHITE_TEXT_THRESHOLD = 0.78

# Typography
FONT_SANS = (
    "-apple-system", "Segoe UI", "Microsoft YaHei", "PingFang SC",
    "Noto Sans CJK SC", "WenQuanYi Micro Hei", "DejaVu Sans", "sans-serif",
)

_CJK_CANDIDATES = [
    "Noto Sans CJK SC", "Noto Sans SC", "Source Han Sans SC",
    "WenQuanYi Micro Hei", "WenQuanYi Zen Hei", "SimHei",
    "Microsoft YaHei", "PingFang SC",
]


def pick_matplotlib_cjk_font() -> str | None:
    """Return first available CJK font, or None."""
    try:
        from matplotlib import font_manager
        available = {f.name for f in font_manager.fontManager.ttflist}
        for name in _CJK_CANDIDATES:
            if name in available:
                return name
    except Exception:
        pass
    return None


def matplotlib_rcparams() -> dict:
    """rcParams dict for professional static charts."""
    cjk = pick_matplotlib_cjk_font()
    sans = ([cjk] if cjk else []) + ["DejaVu Sans"]
    return {
        "font.family": "sans-serif",
        "font.sans-serif": sans,
        "axes.unicode_minus": False,
        "figure.facecolor": "white",
        "axes.facecolor": BG_CARD,
        "axes.edgecolor": BORDER,
        "axes.linewidth": 1.0,
        "axes.grid": True,
        "grid.color": GRID,
        "grid.linewidth": 1.0,
        "axes.axisbelow": True,
        "axes.titlesize": 13,
        "axes.labelsize": 10,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "figure.dpi": 140,
    }


def apply_matplotlib_theme() -> None:
    """Apply theme to matplotlib (call once at module load in plots.py)."""
    import matplotlib.pyplot as plt
    plt.rcParams.update(matplotlib_rcparams())


def plotly_layout_defaults() -> dict:
    """Shared Plotly layout fragment."""
    return {
        "font": {"family": ", ".join(FONT_SANS), "color": INK, "size": 13},
        "paper_bgcolor": "white",
        "plot_bgcolor": BG_CARD,
        "colorway": GAME_COLOR_LIST,
        "margin": dict(l=60, r=30, t=70, b=50),
    }


def plotly_template() -> dict:
    """Plotly template dict for go.Figure.update_layout."""
    return {
        **plotly_layout_defaults(),
        "xaxis": dict(gridcolor=GRID, linecolor=BORDER, zeroline=False),
        "yaxis": dict(gridcolor=GRID, linecolor=BORDER, zeroline=False),
    }


def game_color(game_key: str, index: int = 0) -> str:
    return GAME_COLORS.get(game_key, GAME_COLOR_LIST[index % len(GAME_COLOR_LIST)])


def heatmap_cmap():
    """Matplotlib colormap matching the Plotly heatmap scale (shared identity)."""
    from matplotlib.colors import LinearSegmentedColormap
    return LinearSegmentedColormap.from_list("gacha_heat", list(HEATMAP_ANCHORS))


def watermark_text() -> str:
    return "gacha · powered by GGanalysis"
