# Gacha 抽卡概率分析工具 —— 调研报告 & 项目计划书

> 状态：**M1 + M2 + M3 完成；M4 报告增强(Plotly 交互式 HTML 报告)完成（"更多游戏"按需跳过）**
> 版本：v0.8
> 目标读者：项目发起人（你）
> **核心原则：引擎复用 GGanalysis，精力投入"算得准 / 看得懂 / 比得了"的应用层。任何超出 §4 Scope 的需求走 §7 变更流程，禁止开发中临时夹带。**

---

## 0. TL;DR（一页纸概览）

- **产品愿景**：建立在 **GGanalysis** 之上的抽卡决策与分析工具 —— 把枯燥的概率分布，翻译成玩家能直接决策的直观结论，并支持**跨游戏横向比较**。
- **定位（v0.5 确认）**：**二次开发**。引擎层直接复用 GGanalysis 的精确分布（不重复造轮子）；本项目专注三大支柱：
  1. **算得准**：单目标 / 组合目标（角色+武器卷积）/ 预算↔概率；
  2. **看得懂**：概率曲线、预算-概率曲线、运气分位、资源↔货币↔人民币换算、决策建议；
  3. **比得了**：跨游戏归一化比较（期望抽数 / 期望花费 / 综合概率 / 肝氪指数）。
- **学习副线（保留，不阻塞主线）**：`engine/reference/` 下自研 MC/DP 一份，用作校验 + 讲清原理；`docs/theory/` 写数学推导。
- **技术栈**：Python 优先（CLI + matplotlib 图 + HTML/MD 报告）；Web 后置。
- **防漂移**：Non-Goals（§4.3）+ 模块契约（§6.4）+ 每里程碑 DoD（§7.1）+ 变更流程（§7.3）+ `DECISIONS.md`。
- **本阶段产出**：本文档。下一步启动 M1。

---

## 1. 项目背景与动机

抽卡（gacha）是带「保底（pity）」的离散随机过程，是概率论应用的优质载体。玩家面对的核心痛点是**信息不对称**：手里的资源够不够、抽中的概率多大、自己算欧还是非、哪个游戏更划算 —— 这些都需要把"概率分布"翻译成"可决策的结论"。GGanalysis 已经把"算分布"做到工业级，但缺少面向决策的应用层与跨游戏视角，这正是本项目的切入点。

涉及的概率论（学习副线会逐一讲清，见 `docs/theory/`）：几何/负二项分布、非齐次成功概率（软保底）、吸收马尔可夫链、嵌套条件概率（50/50、捕获明光）、卷积（组合目标）、蒙特卡洛。

---

## 2. 调研结果：现有方案与社区方法

### 2.1 引擎基座：GGanalysis（本项目直接依赖）

`OneBST/GGanalysis`（GitHub 235★，MIT，活跃维护，Python≥3.9，依赖 numpy/scipy/matplotlib）。

- **抽卡层抽象**：`Bernoulli_layer` / `Pity_layer` / `Markov_layer` / `Coupon_Collector_layer`，由 `CommonGachaModel` 复合。
- **核心类型 `FiniteDist`**：对 numpy 数组的封装（FFT/快速幂/缓存优化）。`A * B`=卷积（两随机变量之和→"先抽 A 再抽 B"的总抽数分布），`A ** n`=自卷积（抽 n 个拷贝），暴露 `.dist`/`.exp`/`.var`。
- **已内置游戏**：原神、星铁、绝区零、明日方舟、鸣潮、蔚蓝档案、重返未来1999、少前2、白夜极光、碧蓝航线等。

```python
import GGanalysis.games.genshin_impact as GI
dist = GI.up_5star_character(item_num=3, item_pity=20, up_pity=1)
print(dist.exp, dist.var, dist.dist)
```

> **关键点**：`FiniteDist` 的卷积 `*` 正是实现"角色+武器组合期望"的天然工具 —— `combined = char_dist * weapon_dist`。

### 2.2 其他参考实现（含可复用点）

| 项目 | 方法 | 价值 |
|---|---|---|
| `OneBST/GGanalysis` | 卷积精确解 + 抽卡层 | **引擎基座，直接依赖** |
| `kylechen.net` 文章 | MC + DP（含 numpy 向量化）| 学习副线 reference 引擎蓝本 |
| `MSIsunny/GenshinWishCalculator-py` | 转移矩阵精确解 | 校验对照 |
| `sakan811/gacha-game-pull-calculator` | Go+Vue+Python 多游戏 Web 计算器 | 后期 Web 形态 + 跨游戏比对参考 |
| `rollends.ca` 文章 | 马尔可夫平稳分布反推参数 | 参数自洽性验证 |
| `astral4/aksim` | Rust DP + 基准测试 | 精确算法交叉验证 |
| `mark9804/endfield` | DP/MC 双引擎 + 残留状态折算 | 工程范本 |
| `MSIsunny/...-py` | 转移矩阵精确解 | 马尔可夫法对照 |
| `@allemandi/gacha-engine` | TS 引擎库 | （后期 Web）目标概率↔所需抽数反查 |
| paimon.moe / starrailstation | 数据生态 + 运气分位 + 分布直方图 | 可视化/数据格式范例 |
| **UIGF-Org (uigf.org)** | **UIGF v4.2 抽卡记录标准格式** | **数据互通标准（见 §2.5、CR-1）** |
| HoYoLAB / Wiki | 数据与机制事实来源 | 见 §2.3 |

> 完整调研（25+ 项目、玩家工具、跨游戏经济、概率论方法）见 `docs/RESEARCH.md`。

### 2.3 原神抽卡机制（事实来源）

社区基于大规模数据（genshin-wishes.com 2021 年已 2500 万抽）逆向得出，与官方公示一致。**软保底精确算法官方未公布，模型只要"无穷抽收敛到官方概率 + 拟合实测"即有效，且满足条件的模型不唯一。**

| 机制（角色活动池）| 数值 |
|---|---|
| 5★ 基础 / 综合概率 | 0.6% / ≈1.6% |
| 5★ 软保底 / 硬保底 | 第 74 抽起每抽 +6% / 第 90 抽必出 |
| 4★ 基础 / 硬保底 | 5.1% / 第 10 抽必出 |
| 50/50 | 出 5★ 时 50% 为 UP；歪了则下个 5★ 必 UP（大保底）|
| 捕获明光（v5.0）| 基础 0.018%；连歪 1/2/3 次→33.3%/66.7%/100% 转 UP；UP 综合概率→≈55% |

> 武器池（0.7%/软保底63/硬保底80/定轨）留待后续阶段。

### 2.4 三类方法与关键方法论澄清

- MC（模拟，近似，易扩展）/ 精确法（DP、马尔可夫矩阵、卷积——GGanalysis 用卷积）/ 解析近似。本项目**主用 GGanalysis 卷积精确解**，MC/DP 作校验与教学。

**调研得到的关键澄清（写进实现守则）：**
1. **经验概率 vs 条件概率**：必须区分"长期平均出率"与"每抽真实条件概率"（软保底曲线），图表与文案不得混淆。
2. **软保底反推是欠定问题**：单凭公示综合概率无法唯一确定每抽曲线，需经验分布做形状约束。→ 本项目**直接用社区公认参数，不重新反推**。
3. **捕获明光是带记忆机制**：连歪计数使**卷积法失效**，须用 DP + "连歪计数"维度精确建模。→ 这是自研 reference 引擎相对 GGanalysis 卷积法的**潜在增量**，故 M1 第一步须先验证 GGanalysis 是否已覆盖。
4. **2.6 亿抽级社区数据**佐证：原神平均 ~62 抽出 5★，叠加 50/50 后限定 UP 期望 ≈ 93 抽（≈1.5×单次出金期望）。

### 2.5 抽卡记录数据格式：UIGF v4.2（调研重要发现）

社区由 [UIGF-Org](https://uigf.org) 维护统一抽卡记录交换格式 **UIGF v4.2**，顶层按游戏分区 `hk4e`(原神)/`hkrpg`(星铁)/`nap`(绝区零)，每条记录含 `uigf_gacha_type`/`gacha_type`/`item_id`/`time`/`id`/`rank_type` 等。paimon.moe、HoYo.Gacha 等主流工具均支持导入导出。

- **价值**：支持 UIGF 即可零成本接入整个数据生态，让工具能分析用户**真实抽卡记录**（还原 pity、50/50 胜率、终身抽数），且**仅解析标准 JSON，不碰游戏接口**。
- **陷阱**：`time` 保留原始字符串不转 Date；pity 排序用 `id` 而非本地时间；严格遵守官方 JSON Schema 字段类型。
- **authkey 直接抓取**会触碰游戏接口（与 Non-Goal 冲突）且维护成本高（接口随版本变动），故倾向**以 UIGF 文件为主**。
- 详见 `docs/RESEARCH.md` §2.2-2.3。本能力作为候选 CR-1（§4.4）。

---

## 3. 本项目定位（避免重复造轮子）

> v0.5 重大修订：从"自研引擎"转为"GGanalysis 二次开发 / 应用层"。

**我们做（Value-add，主线）：**
1. **统一封装层**：把 GGanalysis 各游戏模型封装成统一接口，屏蔽差异。
2. **算得准**：组合目标（角色+武器卷积）、预算↔概率、资源↔货币↔人民币换算。
3. **看得懂**：PMF/CDF/预算曲线、运气分位、决策建议、一键报告。
4. **比得了**：跨游戏归一化经济模型与横向比较。

**我们不做（见 §4.3 Non-Goals）：**
- 不重写卷积/分布引擎与 GGanalysis 竞争。
- 不覆盖 GGanalysis 不支持的冷门游戏（以其已支持的为准）。

**学习副线（保留，不阻塞主线）**：`engine/reference/` 自研 MC/DP 用于校验 GGanalysis 一致性 + 教学；`docs/theory/` 写清每个功能背后的数学。

**与 GGanalysis 的关系**：*它是发动机，我们造整车（仪表盘 + 导航 + 对比评测）。*

---

## 4. 项目范围（Scope）与 Non-Goals

### 4.1 MVP（第一阶段，原神角色池打通全链路）—— In Scope

- 封装 GGanalysis 原神角色池 → 统一接口。
- **算得准**：给定状态(垫抽/大保底/明光连歪)与目标 → PMF/CDF/EV/分位数；预算→概率；抽↔原石↔人民币。
- **看得懂**：PMF/CDF 图 + 运气分位 + 文字决策建议 + CLI。
- 学习副线：reference MC 引擎做一致性校验。

### 4.2 后续阶段

- **组合目标**：角色+武器联合期望（卷积），扩展到武器池（定轨）。
- **数据接入（CR-1）**：UIGF v4.2 导入/导出 + 从真实记录还原 pity/胜率/历史统计。
- **跨游戏比对**：接入星铁/绝区零，归一化经济比较 + 比对图。
- **报告/可视化增强**；Web 计算器（另立提案）。

### 4.3 Non-Goals（硬边界，越界即"范围变更"）

1. ❌ 不自研通用分布/卷积库与 GGanalysis 竞争。
2. ❌ 不支持 GGanalysis 未覆盖的游戏。
3. ❌ 不做玩家真实数据采集管线 / 在线服务 / 账号登录 / 抓包 / 与游戏服务器交互。
4. ❌ 不做"必中预测"等违背概率本质的承诺；输出一律标注估计值。
5. ❌ MVP 不做 Web/GUI、不做武器池、不做跨游戏（均属后续阶段）。
6. ❌ 不做与建模无关的运营/商业化分析。
7. ❌ 不做 authkey 直接抓取/与游戏服务器交互（数据以 UIGF 文件导入为准；见 CR-5）。

### 4.4 已纳入的调研增补功能（确认结果 / 详见 `DECISIONS.md` CR 区）

| 编号 | 功能 | 归属 |
|---|---|---|
| CR-1 | **UIGF v4.2 导入/导出 + 真实记录历史统计** | ✅ M2 |
| CR-2 | **Cashback 剩余抽数返还期望** | ✅ M1 |
| CR-3 | **运气分位（理论分布百分位）** | ✅ M1 |
| CR-4 | **尾部风险量化（VaR/CVaR、安全垫）** | ✅ M1（加分）|
| CR-5 | authkey 直接抓取 | ❌ 不做（保持 Non-Goal#7）|

---

## 5. 核心功能与指标

### 5.1 工具要回答的玩家问题

1. 垫了 X 抽、是否大保底，再抽 Y 抽出当期 UP 的概率？
2. 满命角色(C6)+专武(R1) 的期望抽数 / 原石 / 人民币？（组合目标）
3. 有 N 抽预算，拿下目标的概率？90% 把握需多少？
4. 这把 70 抽出货，在玩家中算欧还是非？（运气分位）
5. 原神 vs 星铁 vs 绝区零，抽一个限定，谁更便宜 / 更肝？（跨游戏）

### 5.2 输出指标

PMF、CDF、期望 EV（抽/货币/钱）、分位数（P50/P90/P99）、预算-概率曲线、组合分布、跨游戏对比表与图。
**调研增补指标**：Cashback 剩余抽数返还期望（CR-2）、运气分位（CR-3，结果在理论分布中的百分位）、尾部风险 VaR/CVaR 与安全垫抽数（CR-4）。

### 5.3 跨游戏归一化经济模型（比对的基础，先定清楚）

每个游戏在 `games/` 声明经济参数，统一口径比较：

```python
GameSpec(
    name="原神",
    top_rarity="5★",
    currency_name="原石",
    currency_per_pull=160,      # 1 抽所需货币
    money_per_pull=...,         # 按充值档位估算的每抽人民币（标注口径与来源）
    gg_module=GI,              # 复用 GGanalysis 模型
    banners=["character", "weapon"],
)
```

**归一化指标（SUoV = "一个限定"为单位，按层级）：** ①期望抽数/限定一个（含软硬保底+50/50+UP权重，**不可比基础出率**）②期望货币/限定 ③折算现金/限定（统一"最高性价比常规档位"，排除首充）④每30天白嫖抽数 ⑤白嫖每年可得限定数=年白嫖抽数÷期望抽数（终极慷慨度）⑥产出÷需求（是否追得上版本）。

**8 个不可比的坑（必须处理，详见 `docs/RESEARCH.md` §3.4）：** 基础出率不可直接比（方舟 2% 是"任意6星"被 UP 权重稀释）/ 保底结构不同 / 限定vs常驻 / 角色vs武器 / 队伍构成 / 一次性福利vs长期产出 / 版本长度与口径 / 货币现金档位结构。**比对必须只比限定、统一口径并标注。**

---

## 6. 技术方案

### 6.1 技术栈

- Python 3.12+；依赖 `numpy`/`scipy`/`matplotlib`/`pytest`/**`GGanalysis`**。
- 展示：CLI + matplotlib 图 + HTML/Markdown 报告（Python 优先，Web 后置）。
- 依赖管理：`requirements.txt`（锁版本）。

### 6.2 架构（分层、单向依赖）

```
L3 表现层 viz/cli      图表 / 报告 / 命令行
        │
L2 分析层 analysis     metrics / combine(卷积) / budget(换算) / compare(跨游戏)
        │
L1 游戏层 games        机制+经济参数 + 游戏注册表（跨游戏比对基础）
        │
L0 引擎层 engine       封装 GGanalysis（主）+ reference 自研 MC/DP（校验/教学）
```

依赖方向严格单向向下，禁止反向与跨层。

### 6.3 目录结构

> 下列结构与现状一致（用 `find src -name '*.py'` 自证）。历史版本曾列出未实现的
> `engine/reference/dp.py`、`docs/theory/gacha-math.md`、`notebooks/`（DP 引擎 D18 决定不自研、
> 数学推导文档与 notebooks 未落地，均已删除）；并补回已实现的 `analysis/grid.py`、
> `analysis/compare.py`、`io/`、`games/hsr.py`、`games/zzz.py`、`viz/report.py`。

```
gacha/
├── README.md
├── requirements.txt
├── pyproject.toml
├── docs/
│   ├── PROJECT_PROPOSAL.md
│   ├── DECISIONS.md                 # 防漂移单一事实来源
│   ├── RESEARCH.md                  # M0 深度调研
│   └── games/genshin.md             # 机制事实卡（带来源）
├── src/gacha/
│   ├── __init__.py
│   ├── cli.py                       # 七子命令：games/analyze/combine/history/compare/grid/report
│   ├── engine/
│   │   ├── base.py                  # 统一数据结构 + 接口（契约冻结，§6.4）+ BANNER_* 常量
│   │   ├── gg_adapter.py            # 封装 GGanalysis（主引擎）
│   │   └── reference/               # 学习副线：自研校验/教学引擎
│   │       └── mc.py                # 蒙特卡洛（机制经依赖注入，不反向依赖 games）
│   ├── games/
│   │   ├── base.py                  # GameSpec / BannerSpec / HistoryPolicy
│   │   ├── registry.py              # 游戏注册表（跨游戏比对基础）
│   │   ├── genshin.py               # 原神 机制+经济参数（GameSpec）
│   │   ├── hsr.py                   # 星穹铁道
│   │   └── zzz.py                   # 绝区零
│   ├── analysis/
│   │   ├── metrics.py               # PMF→CDF/EV/分位数 + Cashback/运气分位/VaR-ES(CR-2/3/4)
│   │   ├── combine.py               # 组合目标（角色+武器卷积）
│   │   ├── budget.py                # 预算↔概率、抽↔货币↔人民币
│   │   ├── compare.py               # 跨游戏归一化比对（含不可比护栏）
│   │   └── grid.py                  # 命座×精炼 成本网格
│   ├── io/                          # 数据导入导出（M2）
│   │   ├── uigf.py                  # UIGF v4.x 导入/导出（CR-1，含版本/字段校验）
│   │   └── history.py               # 真实记录→还原 pity/50-50胜率/终身抽数（game-agnostic）
│   └── viz/
│       ├── plots.py                 # PMF/CDF/预算曲线/比对图/成本热力图（matplotlib）
│       └── report.py                # 交互式自包含 HTML 报告（Plotly）
├── tests/                           # 与 GGanalysis 一致性 + 边界用例 + 换算 + 修复回归
└── examples/
    └── uigf_sample.json             # UIGF 样例（供 history 命令演示）
```

### 6.4 模块契约（接口先冻结，防漂移）

```python
# engine/base.py —— 接口冻结，改需走变更流程
from dataclasses import dataclass, field

@dataclass(frozen=True)
class PullState:                 # 当前状态（输入）
    item_pity: int = 0              # 5★ 保底计数
    is_guaranteed: bool = False     # 是否大保底
    radiance_losses: int = 0        # 捕获明光连歪次数

@dataclass(frozen=True)
class Target:                    # 抽卡目标（输入），支持组合
    banner: str = "character"       # character / weapon
    copies: int = 1                 # 需要的拷贝数（C0=1, C6=7, R1=1, R5=5）

@dataclass(frozen=True)
class PullDistribution:         # 统一输出（CDF/EV/分位数由 metrics 派生）
    pmf: "np.ndarray"               # pmf[k]=恰好第 k 抽达成目标的概率

class Solver(Protocol):
    def solve(self, game, state: PullState, target: Target, max_pulls: int) -> PullDistribution: ...

# combine.py：组合目标 = 各分布卷积（复用 GGanalysis FiniteDist 的 *）
def combine(dists: list[PullDistribution]) -> PullDistribution: ...
```

约定：①求解器只产 `PullDistribution`，派生指标统一在 `metrics`；②`games/` 只放数据(机制+经济)不放算法；③新增游戏=新增 `games/*.py`，不改引擎/分析核心。

---

## 7. 防漂移机制

### 7.1 每里程碑 DoD（不达标不进下一阶段）

- **M1 DoD**：原神角色池全链路打通（状态+目标→PMF/CDF/EV/分位数→预算→换算→图+CLI）；engine 封装结果与 GGanalysis 直接调用一致；reference MC 期望误差 <0.5%；pytest 全绿。
- **M2 DoD**：组合目标（角色+武器卷积）正确（与 GGanalysis 卷积结果一致到 1e-9）；武器池接入；**UIGF v4.2 导入→导出往返一致（含时区/id 排序正确），能从真实记录还原 pity/50-50胜率/终身抽数**。
- **M3 DoD**：跨游戏比对（≥2 游戏）归一化口径正确，产出对比表+图。
- **M4 DoD**：新增游戏**仅**改 `games/`，引擎/分析核心零改动（git diff 自证）。

### 7.2 工程守则

依赖严格单向；接口冻结改动需记 `DECISIONS.md`；新功能先问"在 §4 Scope 内吗"，不在则进 backlog；每次提交聚焦单一里程碑；抽卡数值与经济参数集中在 `games/`，禁止魔法数字散落。

### 7.3 变更控制

任何超 §4 的需求 → 记入 `DECISIONS.md` 变更请求区（动机/影响里程碑/处理）→ 发起人确认后才纳入。`DECISIONS.md` 是单一事实来源。

### 7.4 验证

与 GGanalysis 一致性校验；reference MC 落在精确解置信带内；收敛到官方概率（5★≈1.6%、UP≈55%）；边界用例（90 抽必出、10 抽必出 4★、连歪 3 次必 UP）；换算与跨游戏口径单测；MC 固定随机种子。

---

## 8. 里程碑与计划

| 阶段 | 内容 | DoD |
|---|---|---|
| **M0（已完成）** | 调研 + 定位 + 约束 | 本文档 v0.7 + RESEARCH.md + DECISIONS.md |
| M1 ✅ | 骨架 + engine(GG封装) + 原神 config + 全链路(算得准+看得懂) + reference MC 校验 + **Cashback/运气分位/风险指标(CR-2/3/4)** | 已达成 |
| M2 ✅ | 组合目标(角色+武器卷积) + 武器池 + **UIGF v4.2 导入导出 + 真实记录统计(CR-1)** | 已达成（卷积一致 1e-12；UIGF 往返一致）|
| M3 ✅ | 跨游戏比对（接入星铁/绝区零）+ 比对图 | 已达成（HSR/ZZZ 对 GG 一致；归一化口径落地）|
| M4 ✅(部分) | 报告增强（Plotly 交互式 HTML 报告）；"更多游戏"按发起人意见跳过 | 已达成报告增强 |
| M5（可选）| Web 交互计算器（Streamlit 等）| 另立提案 |

---

## 9. 已确认决策

1. 技术栈：✅ Python 优先（CLI+matplotlib+HTML/MD 报告），Web 后置。
2. 侧重点：✅ 研究与工具兼顾。
3. 原神 MVP：✅ 角色活动池打通全链路。
4. 捕获明光：✅ 纳入 MVP。
5. 数据校准：✅ 先用社区参数。
6. **定位（v0.5）：✅ GGanalysis 二次开发 / 应用层为主**；三支柱=算得准/看得懂/比得了。
7. **学习副线：✅ 保留为副线**（engine/reference 自研 MC/DP 校验+教学，docs/theory 写数学），不阻塞主线。
8. 立项理由：GGanalysis 是"计算库"非"工具/教程"，缺决策应用层与跨游戏视角；本项目做整车而非发动机。
9. **调研增补（v0.7）**：✅ 纳入 CR-1 UIGF 导入导出(M2)、CR-2 Cashback、CR-3 运气分位、CR-4 风险量化(M1)；❌ 拒绝 CR-5 authkey 抓取（保持 Non-Goal）。完整调研见 `docs/RESEARCH.md`。

---

## 10. 待定项

- 第二个接入的游戏（M3 前定）：星铁 / 绝区零 / 原神武器池（武器池在 M2 已涉及）。
- 每抽人民币换算的口径与档位来源（M1 经济参数时定）。

**下一步：启动 M1**，第一步先实际安装 GGanalysis 并验证其原神模型是否已含"捕获明光"，再搭骨架。

---

## 附录 A：参考来源

- `OneBST/GGanalysis`（引擎基座，抽卡层+卷积，MIT）及其文档 onebst.github.io/GGanalysis
- kylechen.net《Algorithms for calculating gacha probabilities》（MC+DP 蓝本）
- `MSIsunny/GenshinWishCalculator-py`（转移矩阵精确解）
- `sakan811/gacha-game-pull-calculator`（多游戏 Web 计算器形态）
- rollends.ca《Formally Designing a Gacha System》（马尔可夫平稳分布反推参数）
- HoYoLAB《Statistical model for Genshin Impact's droprates》（74/+6%/90，2500 万抽）
- Genshin Impact Wiki — Wish（官方综合概率、捕获明光 0.018%、≈55% UP）
- B 站《原神抽卡全机制总结》cv10468091

> 免责声明：抽卡内部算法官方未公开，所有模型均为基于公示概率与社区实测的近似；结果为估计值，非保证。本项目仅用于研究与学习，与 HoYoverse 及相关厂商无关。
