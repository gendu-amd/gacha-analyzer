# 可视化设计规范（VIZ_DESIGN）

> 统一静态 matplotlib 与 Plotly HTML 报告的视觉语言。参考 paimon.moe / SRS 类工具的**数据清晰度**，不做游戏 UI 仿制。

## 1. 设计原则

| 原则 | 说明 |
|------|------|
| 数据优先 | 信息密度适中，标注期望/P50/P90/预算线 |
| 非游戏化 | 无卡面、无粒子；专业分析工具美学 |
| 中英分层 | Plotly/HTML 中文；matplotlib 英文主标签 + subtitle 可含中文 |
| 单一来源 | 所有 token 在 `viz/theme.py`，plots/report 只引用 theme |

## 2. 设计 Token（`viz/theme.py`）

### 配色

| Token | 值 | 用途 |
|-------|-----|------|
| BLUE | `#3D6FE5` | PMF/CDF 主曲线、链接色 |
| GREEN | `#1F9E78` | P50、白嫖速率 |
| AMBER | `#E8A317` | 期望值 |
| RED | `#E4572E` | P90 安全垫 |
| PURPLE | `#8E5BD6` | 预算线 |
| INK / MUTED | `#1F2937` / `#6B7280` | 正文 / 次要文字 |
| BG_PAGE / BG_CARD | `#F4F6FA` / `#FBFCFE` | 页面 / 图表区 |

### 游戏序列色

- genshin → BLUE
- hsr → GREEN
- zzz → PURPLE

用于跨游戏 CDF 叠加、柱状图。

### 字体

- **Plotly/HTML**：系统无衬线 + Microsoft YaHei / PingFang SC
- **matplotlib**：运行时探测 Noto Sans CJK SC / WenQuanYi Micro Hei；无则 DejaVu Sans（英文标签）

## 3. 图表类型

| 函数 | 介质 | 说明 |
|------|------|------|
| `plot_pmf_cdf` | PNG | 双子图 PMF+CDF，分位与预算标注 |
| `plot_cost_grid` | PNG | 命座×精炼热力图 YlOrRd |
| `plot_comparison` | PNG | 跨游戏单目标双柱图 |
| `plot_compare_combine_cdf` | PNG | 组合目标 CDF 叠加 + 期望柱图 |
| `pmf_cdf_figure` 等 | HTML | Plotly 交互，复用 theme |

## 4. HTML 报告结构

```
header（标题 + 副标题，蓝色下划线）
section × N（白卡片、圆角、轻阴影）
  ├─ 指标卡 grid
  ├─ 预算块（紫色底）
  ├─ 把握表
  └─ Plotly 图
footer（水印）
```

网格章节可选嵌入单元格 PMF（`--grid-cells 00,01,21,65`），锚点 `id="pmf-CxRy"`。

## 5. 与 STREAMLIT_DESIGN 的关系

Streamlit（M5）应直接 import `viz/theme.py` 与 `viz/report.py` 的 figure 工厂，保持配色一致。

## 6. 变更记录

| 日期 | 变更 |
|------|------|
| 2026-06-27 | 初版：theme.py + plots/report 重构 + compare-combine CDF + grid PMF 导出 |
