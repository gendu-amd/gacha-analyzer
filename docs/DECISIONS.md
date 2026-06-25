# 决策与变更日志（DECISIONS）

> 本文件是项目的**单一事实来源**，用于防止开发漂移。
> 规则：任何超出 `PROJECT_PROPOSAL.md` §4 Scope 的需求，先记到这里的「变更请求」区，由发起人确认后才纳入；否则停留在 backlog。

---

## 已确认决策（Accepted Decisions）

| 编号 | 日期 | 决策 | 理由 |
|---|---|---|---|
| D1 | 2026-06-24 | 技术栈先 Python 引擎，Web 前端后置（M5） | 先把方法论与多方法对比跑通 |
| D2 | 2026-06-24 | 侧重点：研究与工具兼顾，研究优先 | 发起人选择 |
| D3 | 2026-06-24 | 原神 MVP 只做角色活动池 | 先跑通方法论，武器池留 M4 |
| D4 | 2026-06-24 | 捕获明光纳入 MVP | 作为嵌套条件概率的核心案例 |
| D5 | 2026-06-24 | 不自研卷积引擎与 GGanalysis 竞争 | 调研发现 GGanalysis 已工业级，避免重复造轮子 |
| D6 | 2026-06-24 | **采用混合方案**：自研 MC+DP 教学引擎 + GGanalysis 作金标准 oracle + 上层增值 | 发起人确认目标 C（学原理 + 做工具）|
| D7 | 2026-06-24 | 求解器接口与数据结构（PullState/Target/PullDistribution）先冻结 | 防开发漂移，三法结果可直接对比 |
| D8 | 2026-06-24 | **定位转向：GGanalysis 二次开发 / 应用层为主**（取代 D6 的"自研引擎为主"）。三支柱=算得准/看得懂/比得了 | 发起人明确目标为"基于 GGanalysis 二次开发"：组合期望、可视化、跨游戏比对 |
| D9 | 2026-06-24 | 自研 MC/DP 降为**学习副线**（engine/reference + docs/theory），不阻塞主线 | 发起人选 keep_light |
| D10 | 2026-06-24 | 展示形式 **Python 优先**：CLI + matplotlib + HTML/MD 报告；Web 后置 | 发起人选 py_first |
| D11 | 2026-06-24 | 新增四大功能进 Scope：①抽数概率计算器 ②组合目标(角色+武器卷积)期望 ③可视化展示 ④跨游戏归一化比对 | 发起人需求 |
| D12 | 2026-06-24 | 跨游戏比对采用**归一化经济模型**（GameSpec: 货币/单抽货币/单抽人民币）统一口径 | 不同游戏抽数不可直接比，需归一到期望抽数/花费 |

---

## 待定（Open Questions）

| 编号 | 问题 | 何时需要 |
|---|---|---|
| O1 | 第二个接入的游戏选谁（星铁/绝区零）| M3 前 |
| O2 | 每抽人民币换算口径与充值档位来源 | M1 经济参数时 |

---

## 已确认决策（续，来自 M0 深度调研）

| 编号 | 日期 | 决策 | 理由 |
|---|---|---|---|
| D13 | 2026-06-25 | 完成四路并行深度调研，产出 `docs/RESEARCH.md` | 确保前期调研充分 |
| D14 | 2026-06-25 | 交叉验证参照新增：aksim(Rust DP)、mark9804(DP/MC双引擎)、MSIsunny(转移矩阵) | 多源对照保证正确性 |
| D15 | 2026-06-25 | 软保底直接用社区公认参数，**不重新反推**（反推是欠定问题） | 反推需经验分布且对结果无增益 |
| D16 | 2026-06-25 | 明确区分"经验概率 vs 条件概率"，图表/文案不得混淆 | 避免常见统计错误 |
| D17 | 2026-06-25 | 捕获明光用 DP+连歪计数维度建模（卷积法在此失效）；先验证 GGanalysis 是否覆盖 | 带记忆机制，自研 reference 引擎潜在增量 |
| D18 | 2026-06-25 | **M1 验证结论：GGanalysis 0.4.2 已完整支持捕获明光**（`up_5star_character(cr_pity=...)`，`CR_PITY=[0,0.5,0.55,0.95,1]`）。核对：common_5star E=62.30、UP 1个 E=93.45、抽3个 新271.7<旧280.3。故 reference 引擎定位为"教学+独立校验"，无精确性增量 | 实测 GGanalysis API |
| D19 | 2026-06-25 | 运行环境：系统仅 Python 3.6/3.11，采用 **3.11.13 + venv**（GGanalysis 需 ≥3.9）。依赖锁定：GGanalysis 0.4.2 / numpy 2.4.6 / scipy 1.17.1 / matplotlib 3.11.0 / pytest 9.1.1 | 系统无 3.12 |
| D20 | 2026-06-25 | 将 `gacha/` 初始化为独立 git 仓库并首次提交（`.venv`/`out` 已忽略） | 发起人要求初始化仓库 |
| D21 | 2026-06-25 | **图表美化/中文化推迟到后续**（M3 viz 增强或 M5 Web）。当前 matplotlib 英文标签可用 | 发起人决定后续再做 |
| D22 | 2026-06-25 | **跨游戏比对前，先补齐原神所有 GGanalysis 支持的卡池**：新增 常驻池(common_5star)、集录池(classic_up_5star_character)，均对 GGanalysis 逐点验证。集录经查证=经典50/50无捕获明光 | 发起人要求先验证所有卡池 |
| D23 | 2026-06-25 | **新手祈愿推迟**：GGanalysis 无模型、一次性(≤20抽)、无 oracle 可验证、分析价值低 | 发起人确认 later，先做 M3 |
| D24 | 2026-06-25 | M3 接入星铁(星琼)/绝区零(菲林)，跨游戏归一化口径=「抽1个限定/期望抽数·货币·人民币·每月白嫖限定数·相对成本」，GameSpec 增 free_pulls_per_month | 跨游戏比对落地 |
| D25 | 2026-06-25 | ~~CLI 中文表格列对齐受 CJK 双宽字符影响略有错位，推迟~~ → **已解决（2026-06-27）**：`viz/text_width.py`（`unicodedata.east_asian_width`），`viz/tables.py` 用于 CLI 表格 | D25 关闭 |
| D26 | 2026-06-25 | 新增「命座×精炼 成本网格」功能（analysis/grid + 热力图 + CLI grid），属「看得懂」增值层、Scope 内 | 发起人需求 |
| D27 | 2026-06-25 | 方向调整：**跳过「更多游戏」，改做报告增强 + Web/图表化**。引入 Plotly，做交互式自包含 HTML 报告(report 命令)。HTML 路径中文正常 → 部分解决 CR-6（matplotlib 静态图仍英文）| 发起人需求 |

---

## 代码审查修复（2026-06-26，一轮重构修复；不引入新游戏）

> 背景：一次代码审查发现 9 类问题（数值分叉/反向依赖/指标口径/架构泛化/文档漂移/依赖声明/冻结接口登记/一致性健壮性）。以下为修复决策，全部不改变主引擎已验证数值（常驻62.30 / 角色93.45 / 武器86.53 / 星铁89.55；combine 与 GGanalysis 逐点一致）。修复后 pytest 54→71 全绿。

| 编号 | 日期 | 决策 | 理由 |
|---|---|---|---|
| D28 | 2026-06-26 | **自研 MC 复用「大保底→连歪折算」**：`(is_guaranteed and radiance_losses==0) → 初始 losses=1`，与适配层 `_to_gg_kwargs` 同口径 | 修复 MC 与 GG 在 `(copies≥2, guaranteed, losses=0)` 处 ~2% 分叉（实测 155.7→152.63 收敛到 GG 152.63）。新增交叉验证参数堵盲区 |
| D29 | 2026-06-26 | **engine 不得依赖 games（单向铁律）**：`ReferenceMCSolver` 改依赖注入，构造接收 `CharacterMechanism(rate_fn/hard_pity/cr_up_prob)`；由 `games.genshin.genshin_character_mechanism()` 工厂注入，CLI 调用 | 消除 `engine/reference/mc.py` 对 `gacha.games.genshin` 的反向 import（grep 自证零 import），符合 PROPOSAL §6.2 |
| D30 | 2026-06-26 | **截断分布期望/方差/标准差按 total_mass 归一化**（条件于在支持范围内达成），与 `cashback_expected` 同口径；full 分布(mass≈1)不变 | 修复 `max_pulls` 截断时 EV/Var 静默低估；语义在 docstring 写明 |
| D31 | 2026-06-26 | **CVaR 改为严格 Expected Shortfall**（Acerbi–Tasche：对 VaR 原子按 `(α−P(N>VaR))/α` 加权），函数名保留 `conditional_value_at_risk` | 原实现是条件尾期望(CTE)、低估风险；严格 ES 满足 `ES≥CTE≥VaR` |
| D32 | 2026-06-26 | **history 架构泛化为 game-agnostic**：新增 `GameSpec.history_policy`（可选 `HistoryPolicy`：常驻集合 / `character_uigf_gacha_types` / 可靠语言 / 是否捕获明光），`io/history` 改为读取该钩子；**仅原神填充数据，不实现 hsr/zzz 历史**。健壮化：①显式合并 301/400（同时查 uigf_gacha_type 与 gacha_type，避免缺字段被排除）②非中英文 lang 且有 5★ 时 `warnings.warn` 50/50 判定可能不准 | 修复跨游戏断裂 + 硬编码角色名 + 静默误判；不越界做「更多游戏」 |
| D33 | 2026-06-26 | **从直接依赖移除 scipy**（requirements.txt / pyproject.toml 注明为 GGanalysis 传递依赖，本项目零直接使用） | 依赖声明与实际一致；移除后 pytest 仍全绿 |
| D34 | 2026-06-26 | **冻结接口的兼容性增补登记在案**（相对 PROPOSAL §6.4）：`PullDistribution` 增 `source` 字段、`from_finite_dist()` 类方法、`max_pulls` 属性；`Solver` 增 `name` 属性。均为只增不改的向后兼容增补，保持单一事实来源 | 维持「冻结接口改动须记 DECISIONS」纪律（§7.2） |
| D35 | 2026-06-26 | **池子键常量化**：`engine/base.py` 定义 `BANNER_CHARACTER/WEAPON/STANDARD/CHRONICLED`，替换 cli/grid/compare/report/mc/genshin/hsr/zzz 中散落的 "character"/"weapon" 魔法字符串 | 消除静默错配（§7.2 禁魔法数字） |
| D36 | 2026-06-26 | **统一 `max_pulls` 语义**：`<=0`（含缺省）= 自动取合理上限；MC 不再报错，按 `2*hard_pity*copies`（绝对上界）自动兜底；约定写入 `Solver` Protocol docstring | 求解器可无缝替换 |
| D37 | 2026-06-26 | **UIGF 健壮化**：`version` 必须匹配 `^v\d+\.\d+$`（否则 warn）；记录缺必需字段(id/gacha_type)时 warn 并跳过 | 防止静默吃坏数据 |
| D38 | 2026-06-26 | **compare 不可比护栏**：`compare_games` 比较 ≥2 游戏时 `warnings.warn`，每行带 `caveat`「仅供参考」标注（`COMPARE_CAVEAT`） | 把「8 个不可比的坑」从 docstring 落到运行期/返回结构 |

---

## 变更请求（Change Requests，超 Scope 的需求先进这里）

> 格式：CR-编号 | 日期 | 需求 | 动机 | 影响 | 处理（待定/采纳/推迟/拒绝）
> 以下为 M0 调研发现的候选功能，**等发起人确认后**才决定是否纳入及纳入到哪个里程碑。

| 编号 | 需求 | 动机 | 影响 | 处理 |
|---|---|---|---|---|
| CR-1 | **UIGF v4.2 导入/导出**（含历史统计：还原 pity/50-50胜率/终身抽数）| 零成本接入整个数据生态，把工具从"理论"变"能分析你的真实记录"；仅解析标准 JSON，不碰游戏接口 | 新增 `io/uigf.py` 模块 + games 增 uigf_gacha_type 映射 | ✅ **采纳 → M2** |
| CR-2 | **Cashback（剩余抽数返还）期望** | 规划向核心指标，GGanalysis 未封装 | metrics 增能力 | ✅ **采纳 → M1** |
| CR-3 | **运气分位**（结果在理论分布中的百分位）| 情感钩子/传播；不依赖全服数据也能给"理论分位" | metrics 增能力 | ✅ **采纳 → M1** |
| CR-4 | **尾部风险量化**（VaR/CVaR、安全垫抽数）| 最坏情况预算，社区普遍缺 | metrics 加分项 | ✅ **采纳 → M1（加分）** |
| CR-5 | **authkey 直接抓取**（PC 日志读取抽卡链接）| 无 UIGF 文件用户的便捷入口 | 触碰游戏接口，与 Non-Goal#7 冲突；维护成本高 | ❌ **拒绝**（保持 Non-Goal）|
| CR-6 | **图表美化 + 中文化** | 当前图表朴素、图内无中文 | 参考：GGanalysis plot_tools（中文，需思源/Noto CJK 字体）；Web 端可用 chart.js/plotly | ✅ **部分完成**：Plotly HTML 报告中文正常且可交互（D27）；matplotlib 静态 PNG 仍英文 |

---

## 里程碑完成记录（Definition of Done 验收）

| 里程碑 | 状态 | 验收备注 |
|---|---|---|
| M0 调研+定位+约束 | ✅ 完成 | 产出 PROJECT_PROPOSAL.md v0.7 + RESEARCH.md + 本文件 |
| M1 骨架+GG封装+原神全链路+reference校验 +CR-2/3/4 指标 | ✅ 完成 | 全链路打通：算得准(PMF/CDF/EV/分位/Cashback/运气分位/CVaR)+看得懂(图+CLI)+reference MC 校验(误差0.12%)；21 项 pytest 全绿 |
| M2 组合目标(角色+武器卷积)+武器池 +CR-1 UIGF导入导出+真实记录统计 | ✅ 完成 | 武器池(定轨命定值1)+combine(卷积,与GG一致1e-12)+UIGF v4.2往返+history还原(pity/50-50/终身)+CLI combine/history；27 项 pytest 全绿 |
| M3 跨游戏比对(接入星铁/绝区零)+比对图 | ✅ 完成 | 接入 HSR/ZZZ（角色+武器，对 GG 一致1e-12）+ compare 归一化比对(期望抽数/货币/人民币/白嫖限定每月/相对成本)+比对图+CLI compare；46 项 pytest 全绿 |
| M4 报告增强 + Web/图表化 | ✅ 部分完成 | 报告增强：Plotly 交互式自包含 HTML 报告(report 命令，含指标/PMF-CDF/网格/比对，中文正常)；54 项 pytest 全绿。「更多游戏」按发起人意见跳过 |
| 代码审查修复（D28–D38）| ✅ 完成 | 修复 9 类问题（数值收敛/单向依赖/指标口径/history 泛化/文档对齐/依赖声明/冻结接口登记/常量化/max_pulls/UIGF 校验/compare 护栏）；主引擎数值不变；engine 对 games 零 import（grep 自证）；71 项 pytest 全绿（+17）；七子命令冒烟通过 |

---

## 本轮增强（2026-06-27，不引入新游戏）

| 编号 | 日期 | 决策 | 理由 |
|---|---|---|---|
| D39 | 2026-06-27 | ~~**history 50/50 优先 item_id**~~ → **D46 演进**：`detect_standard` 回调封装 item_id + 名字逻辑 | 见 D46 |
| D40 | 2026-06-27 | ~~**reference-MC 范围明确化**~~ → **D47 演进**：`BannerSpec.reference_mc_mechanism` 配置化 | 见 D47 |
| D41 | 2026-06-27 | **跨游戏 compare CNY 折叠**：三游均为 ¥16/抽时，表格与图表不重复逐行人民币，改为统一脚注 + 强调白嫖限定/月与相对成本 | 消除冗余列 |
| D42 | 2026-06-27 | ~~**CJK 终端列宽**~~ → **D48 演进**：格式化迁至 `viz/` 层 | 见 D48 |
| D43 | 2026-06-27 | **Streamlit 设计文档** `docs/STREAMLIT_DESIGN.md`：5 页导航、控件线框、复用映射、MVP 范围；实现留 M5 | 可执行 sprint 蓝图 |
| D44 | 2026-06-27 | **扩展指南** `docs/EXTENSIBILITY.md` + `games/_template.py` 注释模板 | 降低扩展门槛 |
| D45 | 2026-06-27 | **examples/** 参考场景 00/01/21/65 + `run_all.sh` + `states/mid_pity.json` | 可复制基准与验证入口 |

## 架构审查重构（2026-06-27）

| 编号 | 日期 | 决策 | 理由 |
|---|---|---|---|
| D46 | 2026-06-27 | **HistoryPolicy 改为回调**：`detect_standard(record) -> StandardDetection` 替代 `standard_5star_item_ids` / `standard_5star` 字段；原神 `1000` avatar 前缀等逻辑留在 `games/genshin.py` | `io/history` 不再含游戏专属启发式 |
| D47 | 2026-06-27 | **MC 校验配置化**：`BannerSpec.reference_mc_mechanism` 可选工厂；CLI 不再硬编码 `game.key == "genshin"` | 新游戏按需声明，CLI 零改动 |
| D48 | 2026-06-27 | **表格格式化下沉 viz**：`viz/text_width.py` + `viz/tables.py`；`analysis/compare` 与 `analysis/grid` 只产出数据 | 恢复 `analysis` 层纯计算职责 |
| D49 | 2026-06-27 | **games/base 用 Protocol 避免反向依赖**：`HistoryRecord` 协议使 `games` 不 import `io` | 保持单向 `io → games` |

## 卡池覆盖补齐（2026-06-27）

| 编号 | 日期 | 决策 | 理由 |
|---|---|---|---|
| D50 | 2026-06-27 | **星铁常驻跃迁**：新增 `BANNER_STANDARD` → `SR.common_5star`，`has_5050=False`，hard_pity=90，对 GG 逐点验证 | 审计缺口：三游常驻池对齐 |
| D51 | 2026-06-27 | **绝区零常驻频段**：新增 `BANNER_STANDARD` → `ZZZ.common_5star`，参数同星铁 | 同上 |
| D52 | 2026-06-27 | **事实卡文档**：新增 `docs/games/hsr.md`、`docs/games/zzz.md`；README 增三游池子对照总表；genshin.md 补充联动 400/武器 EP 口径 | 单一事实来源，防漂移 |
| D53 | 2026-06-27 | **`BannerSpec.has_5050` 文档化**：字段名保留，docstring 注明武器池可为 75/25（非经典 50/50）；原神 EP 与星铁/ZZZ `up_5star_weapon` 区分 | 诚实标注语义，不改 API |
| D54 | 2026-06-27 | **推迟项登记**：新手池（D23）、4 星池、遗器池 — 三游均未建模，除非 GGanalysis 有 trivial API | 审计透明 |

## 可视化增强 + 能力补齐（2026-06-27）

| 编号 | 日期 | 决策 | 理由 |
|---|---|---|---|
| D55 | 2026-06-27 | **跨游戏组合比对**：`compare --char-copies N --weap-copies M` 调用 `compare_combine_games`，叠加 CDF + 期望柱图（`plot_compare_combine_cdf`） | 填 Q4 缺口：三游 n+n 横向比 |
| D56 | 2026-06-27 | **网格 PMF 批量导出**：`grid --plot-cells` / `--plot-all-cells` / `--export-pmf-dir`，命名 `{game}_{CxRy}.png` | 填 Q5 缺口 |
| D57 | 2026-06-27 | **统一 viz 主题**：新增 `viz/theme.py`（palette / rcParams / plotly template）；`plots.py` + `report.py` 重构引用 | UI 美化 + 防配色漂移 |
| D58 | 2026-06-27 | **HTML 报告样式升级**：header 分隔、指标卡 grid hover、表格斑马纹；`--grid-cells` 嵌入单元格 PMF 锚点 | 报告可读性 |
| D59 | 2026-06-27 | **VIZ_DESIGN.md**：可视化规范文档，与 STREAMLIT_DESIGN 配色对齐 | 单一设计事实来源 |
| D60 | 2026-06-27 | **matplotlib CJK 探测**：theme 运行时尝试 Noto/WenQuanYi，无则保持英文主标签 | 渐进式中文化（CR-6 续） |
