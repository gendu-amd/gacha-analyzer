"""Unified design tokens for matplotlib static plots and Plotly HTML reports.

Professional data-tool aesthetic (paimon.moe / SRS clarity inspired, not game UI).
"""

from __future__ import annotations

import os
import tempfile

# Ensure matplotlib cache is writable before any mpl import elsewhere.
os.environ.setdefault("MPLCONFIGDIR", os.path.join(tempfile.gettempdir(), "gacha-mpl"))

# ---- Palette (professional analytics SaaS, 七麦/Qimai-inspired: calm, coherent) ----
BLUE = "#2E5BFF"
BLUE_FILL = "#C7D7FB"
BLUE_LIGHT = "#EAF0FE"
GREEN = "#16B286"
GREEN_FILL = "#B7E7D6"
AMBER = "#F2A341"
RED = "#E5484D"
PURPLE = "#7A5AF0"
INK = "#1A2333"
MUTED = "#6B7686"
BORDER = "#E5E8EF"
GRID = "#EDF0F5"
BG_PAGE = "#F5F7FB"
BG_CARD = "#FFFFFF"
BG_ACCENT = "#F5F8FE"
WATERMARK = "#AEB6C4"

# Per-game series colors (cross-game charts)
GAME_COLORS = {
    "genshin": BLUE,
    "hsr": GREEN,
    "zzz": PURPLE,
}
GAME_COLOR_LIST = [BLUE, GREEN, PURPLE, AMBER, RED]

# Heatmap — single source of truth shared by matplotlib (PNG) and Plotly (HTML).
# Smooth WARM sequential ramp (cream → amber → red): higher cost = hotter.
# A single warm hue family avoids the cool→warm "断层" (banding) of a blue start.
HEATMAP_ANCHORS = ("#FCF7EE", "#F7D58A", "#F0A24E", "#E06A3D", "#D5452E")
HEATMAP_SCALE_PLOTLY = [
    [0.0, "#FCF7EE"], [0.25, "#F7D58A"], [0.5, "#F0A24E"],
    [0.75, "#E06A3D"], [1.0, "#D5452E"],
]
# Above this fraction of the max value, cells are dark enough to need white text.
HEATMAP_WHITE_TEXT_THRESHOLD = 0.62

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


def rgba(hex_color: str, alpha: float) -> str:
    """Convert ``#RRGGBB`` to a Plotly/CSS ``rgba(r,g,b,a)`` string for light fills."""
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r},{g},{b},{alpha})"


def heatmap_cmap():
    """Matplotlib colormap matching the Plotly heatmap scale (shared identity)."""
    from matplotlib.colors import LinearSegmentedColormap
    return LinearSegmentedColormap.from_list("gacha_heat", list(HEATMAP_ANCHORS))


def watermark_text() -> str:
    return "gacha · powered by GGanalysis"
