# Gacha 抽卡概率分析工具

> 把枯燥的概率分布，翻译成能直接决策的一句话结论 —— 还能跨游戏横向比较。

抽卡是带「保底」的随机过程，算清楚并不容易。本工具建立在成熟的概率引擎 [GGanalysis](https://github.com/OneBST/GGanalysis) 之上，专注三件事：

- **算得准** — 单目标 / 组合目标（角色+武器）/ 预算 ↔ 概率
- **看得懂** — 概率曲线、运气分位、原石/人民币换算、可交互 HTML 报告
- **比得了** — 原神 / 星铁 / 绝区零 同口径横向对比

支持原神（4 卡池）、星穹铁道、绝区零（各 3 卡池，含常驻）。

---

## 它能回答什么

- 我垫了 X 抽、是否大保底，再抽 Y 抽出当期 UP 的概率有多大？
- 抽满命 / 多个拷贝，期望要多少抽 / 原石 / 人民币？
- 有 N 抽预算，把握有多少？想要 90% 把握得攒多少？
- 这把出货，我比多少人更欧？（运气分位）
- 最坏情况要准备多少？（P90 安全垫 / CVaR）

---

## 安装

需要 Python ≥ 3.9（在 3.11 验证）。

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

## 跑通第一个例子

最常见的问题：「原神角色池，从零开始抽 1 个 UP 5★，90 抽够不够？」

```bash
gacha analyze --copies 1 --budget 90
```

输出（节选）会告诉你：

```
== 原神 · 角色活动祈愿 ==
[算得准] 核心指标
  期望抽数 E[N]      : 93.45 抽（≈ 14951 原石，≈ ¥1495）
  中位数 P50         : 80 抽
  P90               : 155 抽（安全垫）
[看得懂] 预算 90 抽 → 达成把握 59.39%
        90% 把握需 155 抽 ...
```

**怎么读**：平均要约 93 抽；但只要 80 抽就有一半人能出（中位数 < 期望，因为少数非酋拉高了平均）；90 抽预算大约六成把握；想要 90% 稳出，得准备 155 抽。

加 `--plot out/up5.png` 会另存一张 PMF + CDF 图：

```bash
gacha analyze --copies 1 --budget 90 --plot out/up5.png
```

---

## 进阶用法

按需要逐步深入。

### 换卡池 / 带当前水位

```bash
# 大保底状态下再抽
gacha analyze --copies 1 --guaranteed --budget 90

# 武器池（定轨）/ 常驻池（任意5★）/ 集录池（经典50/50）
gacha analyze --banner weapon --copies 1 --guaranteed
gacha analyze --banner standard --copies 1
gacha analyze --banner chronicled --copies 1

# 抽满命 C6（7 个拷贝）
gacha analyze --copies 7
```

### 组合目标（角色 + 武器）

```bash
gacha combine --char-copies 1 --weap-copies 1 --budget 250
```

### 导入历史记录（UIGF）

```bash
# 还原当前水位 + 历史统计，并基于水位预测再抽 1 个 UP
gacha history --file examples/uigf_sample.json --predict 1
```

### 跨游戏比对

```bash
# 期望抽数 / 花费 / 白嫖速率
gacha compare --plot out/compare.png

# 组合目标（n 角色 + m 武器，三游 CDF 叠加）
gacha compare --char-copies 1 --weap-copies 1 --plot out/compare_01.png

# 切换游戏
gacha analyze --game hsr --banner standard --copies 1
gacha analyze --game zzz --banner standard --copies 1
```

### 命座×精炼成本网格

```bash
gacha grid --plot out/grid.png
gacha grid --cells 00,01,21,65 --cells-dir out/pmfs/
```

### 交互式 HTML 报告

一份自包含、可交互、中文正常、双击即开的报告（指标 + 分布 + 网格 + 跨游戏比对）：

```bash
gacha report --copies 1 --budget 90 -o out/report.html
```

### 自研蒙特卡洛交叉校验（教学/验证）

```bash
gacha analyze --copies 1 --guaranteed --budget 90 --mc
```

### 参考场景一键跑

```bash
bash examples/run_all.sh   # 见 examples/README.md
```

**常用参数**：`--game`（默认 genshin）、`--banner`（默认 character）、`--copies`、`--pity`（已垫抽数）、`--guaranteed`（大保底）、`--losses`（捕获明光连歪 0~3）、`--budget`、`--plot`、`--mc`、`--mc-runs`。

---

## 卡池对照（参考）

| 游戏 | `--game` | 卡池 | `--banner` | 机制要点 | 历史还原 |
|---|---|---|---|---|---|
| 原神 | `genshin`（默认）| 角色活动祈愿 | `character` | 50/50 + 捕获明光 | ✅ UIGF |
| 原神 | | 武器活动祈愿 | `weapon` | 75/25 + EP 定轨 | — |
| 原神 | | 常驻祈愿 | `standard` | 任意 5★，无 50/50 | — |
| 原神 | | 集录祈愿 | `chronicled` | 经典 50/50，无定轨 | — |
| 原神 | | 联动/双限定(400) | `character` | 与 301 合池，无独立模型 | ✅ 合并 301/400 |
| 星铁 | `hsr` | 角色活动跃迁 | `character` | 50/50，无捕获明光 | — |
| 星铁 | | 光锥活动跃迁 | `weapon` | 75/25，非 EP | — |
| 星铁 | | 常驻跃迁 | `standard` | 任意 5★ | — |
| 绝区零 | `zzz` | 独家频段(角色) | `character` | 50/50 | — |
| 绝区零 | | 音擎频段(武器) | `weapon` | 75/25，非 EP | — |
| 绝区零 | | 常驻频段 | `standard` | 任意 S 级 | — |

- **武器池口径**：仅原神为 EP 定轨（`up_5star_ep_weapon`）；星铁光锥与绝区零音擎为经典 `up_5star_weapon`（75/25 + 大保底，无定轨）。
- **范围外**（三游共通）：新手池、4 星独立池、遗器/圣遗物池 — 未建模（GGanalysis 无现成模型，见 `docs/DECISIONS.md` D23）。

---

## 架构（分层、单向依赖）

```
viz / cli            图表 / 报告 / 命令行
   │
analysis             metrics(PMF/CDF/EV/分位/Cashback/运气分位/VaR·ES) + combine(卷积) + budget + compare/grid
   │
io                   UIGF v4.x 导入导出 + 真实记录还原（pity / 50-50 / 终身抽数，game-agnostic）
   │
games                机制 + 经济参数（GameSpec/BannerSpec/HistoryPolicy）+ 注册表
   │
engine               gg_adapter（封装 GGanalysis，主引擎）+ reference/mc（自研校验/教学）
```

- **engine**：主引擎封装 GGanalysis 的精确卷积解；`reference/` 下自研蒙特卡洛仅作独立校验与教学。严格单向依赖：engine 不 import games。
- **games**：每个游戏一份声明式配置，新增游戏 ≈ 新增一个 `games/*.py`。见 `docs/EXTENSIBILITY.md`。
- **analysis**：所有派生指标集中于此，与求解器解耦。
- **viz**：PNG（matplotlib）与 HTML（Plotly）两种渲染器共用一份取数层（`viz/figdata.py`）与设计 token（`viz/theme.py`），配色/分位/截断逻辑只写一遍。

更深入：方法论与范围见 [`docs/PROJECT_PROPOSAL.md`](docs/PROJECT_PROPOSAL.md)、决策日志 [`docs/DECISIONS.md`](docs/DECISIONS.md)、社区调研 [`docs/RESEARCH.md`](docs/RESEARCH.md)、扩展指南 [`docs/EXTENSIBILITY.md`](docs/EXTENSIBILITY.md)。各游戏机制事实卡：[`genshin`](docs/games/genshin.md) · [`hsr`](docs/games/hsr.md) · [`zzz`](docs/games/zzz.md)。

> 说明：[`docs/STREAMLIT_DESIGN.md`](docs/STREAMLIT_DESIGN.md) 是 Web 交互版的**设计蓝图，尚未实现**。

---

## 验证

```bash
pytest    # 95 项：多游戏多卡池与 GGanalysis 一致性 + MC 交叉校验 + 边界 + 卷积/UIGF/history/compare/grid/report
```

关键校验：自研 MC 与 GGanalysis 期望相对误差 < 0.5%；1 个 UP 5★ 期望 ≈ 93.45 抽；单 5★ ≈ 62.3 抽；硬保底 180 抽内必达成。

## 说明

- GGanalysis 0.4.2 已支持原神「捕获明光」(v5.0)，本工具默认采用含该机制的模型。
- 抽卡内部算法官方未公开，所有模型均为基于公示概率与社区实测的近似；结果为估计值，非保证。
- 本项目仅用于研究与学习，与 HoYoverse 及相关厂商无关。
