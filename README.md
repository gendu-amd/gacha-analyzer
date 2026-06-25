# Gacha 抽卡概率分析工具

建立在 [GGanalysis](https://github.com/OneBST/GGanalysis) 之上的抽卡决策与分析工具：把枯燥的概率分布，翻译成能直接决策的直观结论，并（后续）支持跨游戏横向比较。

三大支柱：**算得准 / 看得懂 / 比得了**。当前进度：**M1（原神全链路）+ M2（武器/组合/UIGF）+ M3（星铁·绝区零接入 + 跨游戏比对）已完成**。已覆盖原神 4 卡池 + 星铁/绝区零 各 3 卡池（含常驻）。

> 完整方法论与范围见 [`docs/PROJECT_PROPOSAL.md`](docs/PROJECT_PROPOSAL.md)；决策日志见 [`docs/DECISIONS.md`](docs/DECISIONS.md)；社区调研见 [`docs/RESEARCH.md`](docs/RESEARCH.md)；扩展指南见 [`docs/EXTENSIBILITY.md`](docs/EXTENSIBILITY.md)。各游戏机制事实卡：[`genshin`](docs/games/genshin.md) · [`hsr`](docs/games/hsr.md) · [`zzz`](docs/games/zzz.md)。

## 三游池子对照总表

| 游戏 | CLI `--game` | 卡池 | `--banner` | 机制要点 | GGanalysis | 历史还原 |
|---|---|---|---|---|---|---|
| 原神 | `genshin`（默认）| 角色活动祈愿 | `character` | 50/50 + 捕获明光 | `up_5star_character` | ✅ UIGF |
| 原神 | | 武器活动祈愿 | `weapon` | **75/25 + EP 定轨** | `up_5star_ep_weapon` | — |
| 原神 | | 常驻祈愿 | `standard` | 任意 5★，无 50/50 | `common_5star` | — |
| 原神 | | 集录祈愿 | `chronicled` | 经典 50/50，无定轨 | `classic_up_5star_character` | — |
| 原神 | | 联动/双限定(400) | `character` | 与 301 合池，无独立模型 | 同角色池 | ✅ 合并 301/400 |
| 星铁 | `hsr` | 角色活动跃迁 | `character` | 50/50，无捕获明光 | `up_5star_character` | — |
| 星铁 | | 光锥活动跃迁 | `weapon` | **75/25，非 EP** | `up_5star_weapon` | — |
| 星铁 | | 常驻跃迁 | `standard` | 任意 5★ | `common_5star` | — |
| 绝区零 | `zzz` | 独家频段(角色) | `character` | 50/50 | `up_5star_character` | — |
| 绝区零 | | 音擎频段(武器) | `weapon` | **75/25，非 EP** | `up_5star_weapon` | — |
| 绝区零 | | 常驻频段 | `standard` | 任意 S 级 | `common_5star` | — |

**推迟 / 范围外**（三游共通）：新手池（GGanalysis 无模型，见 D23）、4 星独立池、遗器/圣遗物池 — 未建模，除非未来有 trivial API。

**武器池口径**：仅原神为 EP 定轨（`up_5star_ep_weapon`）；星铁光锥与绝区零音擎为经典 `up_5star_weapon`（75/25 + 大保底，无定轨）。

## 它能回答什么

- 我垫了 X 抽、是否大保底，再抽 Y 抽出当期 UP 的概率？
- 抽满命角色 / 多个拷贝的期望抽数 / 原石 / 人民币？
- 有 N 抽预算，达成把握多少？要 90% 把握得攒多少？
- 这把 X 抽出货，比多少人更欧？（运气分位）
- 最坏情况要准备多少（P90 安全垫 / CVaR）？

## 安装

环境：Python ≥ 3.9（仓库在 3.11 验证）。

```bash
cd gacha
python3.11 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

## 使用

```bash
# 列出已注册游戏
gacha games

# 原神角色池：抽 1 个 UP 5★，从零开始，给定 90 抽预算，并出图
gacha analyze --copies 1 --budget 90 --plot out/up5.png

# 大保底状态，并用自研蒙特卡洛交叉校验（仅原神角色池；武器池 EP 定轨无 MC）
gacha analyze --copies 1 --guaranteed --budget 90 --mc

# 抽满命 C6（7 个拷贝）的成本
gacha analyze --copies 7

# 其它卡池：武器池(weapon,定轨) / 常驻池(standard,任意5★) / 集录池(chronicled,经典50/50)
gacha analyze --banner weapon --copies 1 --guaranteed
gacha analyze --banner standard --copies 1
gacha analyze --banner chronicled --copies 1

# 组合目标：角色 + 武器 联合期望
gacha combine --char-copies 1 --weap-copies 1 --budget 250

# 导入 UIGF 抽卡记录，还原水位 + 历史统计，并基于当前水位预测
gacha history --file examples/uigf_sample.json --predict 1

# 参考场景（00/01/21/65 命座×精炼编码）— 见 examples/README.md
bash examples/run_all.sh

# 跨游戏比对（原神 / 星铁 / 绝区零）：期望抽数 / 花费 / 白嫖速率
gacha compare --plot out/compare.png

# 跨游戏组合比对（n 角色 + m 武器，三游 CDF 叠加）
gacha compare --char-copies 1 --weap-copies 1 --plot out/compare_01.png

# 星铁 / 绝区零常驻池（任意 5★/S 级）
gacha analyze --game hsr --banner standard --copies 1
gacha analyze --game zzz --banner standard --copies 1

# 命座×精炼 成本网格（联合期望抽数/人民币）+ 热力图
gacha grid --plot out/grid.png
gacha grid --plot-cells 00,01,21,65 --export-pmf-dir out/pmfs/
gacha grid --game hsr --char-pity 50 --char-guaranteed   # 可代入当前水位/换游戏

# 交互式 HTML 报告（指标+分布+网格+跨游戏比对，自包含/可交互/中文正常，双击即开）
gacha report --copies 1 --budget 90 -o out/report.html
```

参数：`--game`（默认 genshin）、`--banner`（默认 character）、`--copies`、`--pity`（已垫抽数）、
`--guaranteed`（大保底）、`--losses`（捕获明光连歪 0~3）、`--budget`、`--plot`、`--mc`、`--mc-runs`。

## 架构（分层、单向依赖）

```
viz / cli            图表 / 报告 / 命令行（analyze / combine / history / games）
   │
analysis             metrics(PMF/CDF/EV/分位数/Cashback/运气分位/VaR·ES) + combine(卷积) + budget(换算) + compare/grid
   │
io                   UIGF v4.x 导入导出(含版本/字段校验) + 真实记录还原(pity/50-50/终身抽数, game-agnostic)
   │
games                机制 + 经济参数（GameSpec/BannerSpec/HistoryPolicy）+ 注册表
   │
engine               gg_adapter(封装 GGanalysis，主) + reference/mc(自研校验/教学)
```

- **engine**：主引擎封装 GGanalysis 精确卷积解；`reference/` 下自研蒙特卡洛仅作独立校验与教学。**严格单向依赖**：engine 不 import games，MC 所需机制由上层依赖注入（`CharacterMechanism`）。
- **games**：每个游戏一份声明式配置，新增游戏 ≈ 新增一个 `games/*.py`；池子键统一用 `BANNER_*` 常量。见 [`docs/EXTENSIBILITY.md`](docs/EXTENSIBILITY.md)。
- **analysis**：所有派生指标集中于此，与求解器解耦；截断分布的 EV/方差按覆盖质量归一化（条件期望）。

## 验证

```bash
pytest            # 80+ 项：多游戏多卡池与 GGanalysis 一致性 + MC 交叉校验 + 边界 + 卷积/UIGF/history/compare/grid/report + 审查修复回归
```

关键校验：自研 MC 与 GGanalysis 期望相对误差 < 0.5%；1 个 UP 5★ 期望 ≈ 93.45 抽；单 5★ ≈ 62.3 抽；硬保底 180 抽内必达成。

## 说明

- GGanalysis 0.4.2 已支持原神「捕获明光」(v5.0)，本工具默认采用含该机制的模型。
- 抽卡内部算法官方未公开，所有模型均为基于公示概率与社区实测的近似；结果为估计值，非保证。
- 本项目仅用于研究与学习，与 HoYoverse 及相关厂商无关。
